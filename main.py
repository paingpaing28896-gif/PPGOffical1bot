import os
import logging
import pytesseract
from PIL import Image
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN မရှိပါ။")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်တို့၏ PPG Post ကို Group/Channel များတွင် Share ထားသော Screenshot ပုံကို ပို့ပေးပါ။ စစ်ဆေးပေးပါမည်။"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ထဲရှိ စာသားများကို စစ်ဆေးနေပါသည်...")
    
    try:
        # Telegram မှ ပုံကို ဒေါင်းလုဒ်ဆွဲခြင်း
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Image Processing
        image = Image.open(io.BytesIO(image_bytes))
        
        # Tesseract OCR ဖြင့် စာလုံးဖတ်ခြင်း (AI Block မရှိပါ)
        detected_text = pytesseract.image_to_string(image).upper()
        
        logging.info(f"Detected Text: {detected_text}")
        
        # 'PPG' ပါမပါ အတိအကျ စစ်ဆေးခြင်း
        if "PPG" in detected_text:
            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                "🎁 သင်တောင်းဆိုထားသော Link ဖြစ်ပါတယ် -\n"
                "https://t.me/+8XdZgmVwrvwyZGVl"
            )
        else:
            await status_msg.edit_text(
                "❌ PPG Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG' သို့မဟုတ် 'Forwarded from PPG' စာတန်း ပါသော ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text("❌ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။ ပုံကို ပြန်လည် ပို့ပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running with Tesseract OCR...")
    app.run_polling()
