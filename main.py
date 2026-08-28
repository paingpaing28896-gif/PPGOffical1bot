import os
import logging
import requests
import io
import time
from PIL import Image, ImageEnhance
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OCR_API_KEY = "K88605900588957"

# သင့် Channel ရဲ့ Chat ID
CHANNEL_CHAT_ID = "-1003790274194"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN မရှိပါ။")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်တို့၏ PPG Post ကို Group/Channel များတွင် Share ထားသော Screenshot ပုံကို ပို့ပေးပါ။ စစ်ဆေးပေးပါမည်။"
    )

def enhance_image_for_ocr(image_bytes):
    """ မှောင်နေသော နောက်ခံမှ စာလုံးအသေးများကို OCR တိကျစွာ ဖတ်နိုင်အောင် ပုံကို ပြုပြင်ပေးခြင်း """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    # ပုံကို ၃ ဆ ပိုကြီးအောင် Zoom ဆွဲခြင်း
    width, height = img.size
    img_resized = img.resize((width * 3, height * 3), Image.Resampling.LANCZOS)
    
    # Contrast တင်ပေးခြင်း
    enhancer = ImageEnhance.Contrast(img_resized)
    img_enhanced = enhancer.enhance(2.5)
    
    # Sharpness တင်ပေးခြင်း
    sharpness = ImageEnhance.Sharpness(img_enhanced)
    img_final = sharpness.enhance(2.5)
    
    output_io = io.BytesIO()
    img_final.save(output_io, format='JPEG', quality=100)
    return output_io.getvalue()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ထဲရှိ စာသားများကို စစ်ဆေးနေပါသည်...")
    
    try:
        # Telegram ထံမှ ပုံဒေါင်းလုဒ်ဆွဲခြင်း
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # ပုံကို ပြတ်သားအောင် ပြုပြင်ခြင်း
        processed_bytes = enhance_image_for_ocr(image_bytes)
        
        # OCR.space API သို့ ပို့ပေးခြင်း
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename.jpg': io.BytesIO(processed_bytes)},
            data={
                'apikey': OCR_API_KEY,
                'language': 'eng',
                'isOverlayRequired': False,
                'OCREngine': 2,
                'scale': True,
                'isTable': True
            },
            timeout=30
        )
        
        result = response.json()
        parsed_results = result.get('ParsedResults', [])
        detected_text = ""
        if parsed_results:
            detected_text = parsed_results[0].get('ParsedText', '')
            
        logging.info(f"Detected Text: {detected_text}")
        text_upper = detected_text.upper()
        
        # စာလုံး စစ်ဆေးခြင်း
        keywords = ["PPG", "FORWARDED", "ADS", "P.P.G"]
        is_matched = any(kw in text_upper for kw in keywords)

        if is_matched:
            # ၁ ယောက်ပဲ ဝင်လို့ရပြီး မိနစ် ၂၀ အကြာတွင် သက်တမ်းကုန်မည့် One-time Link ဖန်တီးခြင်း
            expire_timestamp = int(time.time()) + 1200  
            
            single_use_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_CHAT_ID,
                member_limit=1,           
                expire_date=expire_timestamp 
            )

            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                "🎁 သင်တောင်းဆိုထားသော Link ဖြစ်ပါတယ် -\n"
                f"{single_use_link.invite_link}\n\n"
                "⚠️ *ဤ Link သည် လူတစ်ယောက်အတွက် ၁ ကြိမ်သာ အသုံးပြုနိုင်ပြီး မိနစ် (၂၀) အတွင်း သက်တမ်းကုန်ပါမည်။*",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(
                "❌ PPG/PPG Ads Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG Ads' စာတန်း ပါရှိသည့် ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text("❌ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။ (Bot ကို Channel တွင် Admin ခန့်ထားပြီး 'Add Users' Permission ပေးထားရန် လိုအပ်ပါသည်)")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running with Channel ID & One-time Link...")
    app.run_polling()
