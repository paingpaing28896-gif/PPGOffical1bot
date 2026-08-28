import os
import logging
import requests
import io
import time
from PIL import Image, ImageEnhance, ImageOps
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OCR_API_KEY = "K88605900588957"
CHANNEL_CHAT_ID = "-1003790274194"

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN မရှိပါ။")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်တို့၏ PPG Post ကို Group/Channel များတွင် Share ထားသော Screenshot ပုံကို ပို့ပေးပါ။ စစ်ဆေးပေးပါမည်။"
    )

def preprocess_image(image_bytes):
    """ ပုံရဲ့ အရောင် ဘာရောင်ပဲဖြစ်ဖြစ် စာလုံးပေါ်အောင် ပြင်ဆင်ပေးသည့် Function """
    img = Image.open(io.BytesIO(image_bytes)).convert('L') # Grayscale ပြောင်းခြင်း
    
    # Contrast နှင့် Brightness မြှင့်ပေးခြင်း
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95)
    return output.getvalue()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ထဲရှိ စာသားများကို စစ်ဆေးနေပါသည်...")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # ပုံကို ဘာအရောင်ဖြစ်ဖြစ် စာလုံးရှင်းအောင် ကြိုတင်ပြင်ဆင်ခြင်း
        processed_image = preprocess_image(image_bytes)
        
        # OCR API ပို့ပေးခြင်း
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename.jpg': io.BytesIO(processed_image)},
            data={
                'apikey': OCR_API_KEY,
                'language': 'eng',
                'isOverlayRequired': False,
                'OCREngine': 2,
                'scale': True
            },
            timeout=30
        )
        
        result = response.json()
        parsed_results = result.get('ParsedResults', [])
        detected_text = ""
        if parsed_results:
            detected_text = parsed_results[0].get('ParsedText', '').upper()
            
        logging.info(f"Detected Text: {detected_text}")
        
        # PPG စာတန်း ပါမပါ စစ်ဆေးခြင်း
        if "PPG" in detected_text:
            # မိနစ် ၂၀ သက်တမ်းရှိပြီး ၁ ယောက်ပဲ ဝင်လို့ရမည့် One-time Invite Link ထုတ်ပေးခြင်း
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
                "❌ PPG Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG' သို့မဟုတ် 'Forwarded from PPG' စာတန်း ပါသော ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text("❌ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running...")
    app.run_polling()
