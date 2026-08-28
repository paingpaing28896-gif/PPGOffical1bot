import os
import logging
import requests
import io
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OCR_API_KEY = "K88605900588957"

# သင့် Channel ရဲ့ ID ကို ထည့်သွင်းထားသည်
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
        # Telegram မှ ပုံဒေါင်းလုဒ်ဆွဲခြင်း
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # OCR.space API သို့ စာလုံးဖတ်ရန် ပို့ပေးခြင်း
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'filename.jpg': io.BytesIO(image_bytes)},
            data={
                'apikey': OCR_API_KEY,
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
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
        
        # 'PPG' စာတန်း ပါမပါ စစ်ဆေးခြင်း
        if "PPG" in detected_text:
            # ၅ မိနစ် သက်တမ်းရှိပြီး ၁ ယောက်ပဲ ဝင်လို့ရမည့် One-time Invite Link ဖန်တီးခြင်း
            expire_timestamp = int(time.time()) + 300  # ၅ မိနစ် သက်တမ်း
            
            single_use_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_CHAT_ID,
                member_limit=1,           # လူ ၁ ယောက်သာ ဝင်ခွင့်ပြုမည်
                expire_date=expire_timestamp # ၅ မိနစ်ကျော်ပါက Link ပျက်မည်
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
                "❌ PPG Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG' သို့မဟုတ် 'Forwarded from PPG' စာတန်း ပါသော ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text(
            "❌ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။\n"
            "*(ကျေးဇူးပြု၍ Bot အား Tha Zin Oo Channel ထဲတွင် Admin ခန့်ထားပြီး 'Add Users' / 'Invite via Link' Permission ပေးထားပါ)*",
            parse_mode="Markdown"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running with One-time Link system...")
    app.run_polling()
