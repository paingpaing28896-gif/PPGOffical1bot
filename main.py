import os
import logging
import requests
import io
import time
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

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ထဲရှိ စာသားများကို စစ်ဆေးနေပါသည်...")
    
    try:
        # Telegram ထံမှ ပုံဒေါင်းလုဒ်ဆွဲခြင်း
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # OCR.space API သို့ စာလုံးဖတ်ရန် ပို့ပေးခြင်း (Engine 2 ဖြင့် စာလုံးအသေးများကိုပါ ဖတ်ရှုမည်)
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename.jpg': io.BytesIO(image_bytes)},
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
        
        # စာလုံးဖတ်ရှုရရှိသည့် ရလဒ်များ
        parsed_results = result.get('ParsedResults', [])
        detected_text = ""
        if parsed_results:
            detected_text = parsed_results[0].get('ParsedText', '')
            
        logging.info(f"Detected Text: {detected_text}")
        
        text_upper = detected_text.upper()
        
        # PPG သို့မဟုတ် PPG ADS ပါဝင်ခြင်း ရှိ/မရှိ စစ်ဆေးခြင်း
        # OCR က G ကို C, 6 သို့မဟုတ် Q လို့ မှားဖတ်မိရင်လည်း လက်ခံမည်
        valid_keywords = [
            "PPG", "PPG ADS", "PPGADS", "P.P.G", 
            "PPC", "PPC ADS", "PP6", "PP6 ADS"
        ]
        
        is_matched = any(keyword in text_upper for keyword in valid_keywords)

        if is_matched:
            # ၅ မိနစ် သက်တမ်းရှိပြီး ၁ ယောက်ပဲ ဝင်လို့ရမည့် One-time Invite Link ဖန်တီးခြင်း
            expire_timestamp = int(time.time()) + 300  
            
            single_use_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_CHAT_ID,
                member_limit=1,           
                expire_date=expire_timestamp 
            )

            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                "🎁 သင်တောင်းဆိုထားသော ဝင်ရောက်ရန် Link ဖြစ်ပါတယ် -\n"
                f"{single_use_link.invite_link}\n\n"
                "⚠️ *ဤ Link သည် လူတစ်ယောက်အတွက် ၁ ကြိမ်သာ အသုံးပြုနိုင်ပြီး (၅) မိနစ်အတွင်း သက်တမ်းကုန်ပါမည်။*",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(
                "❌ PPG/PPG Ads Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG Ads' စာတန်း တိကျစွာ ပါရှိသည့် ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text("❌ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။ ပုံကို ပြန်လည် ပို့ပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running with PPG & PPG Ads Detector...")
    app.run_polling()
