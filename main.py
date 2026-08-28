import os
import logging
import easyocr
import numpy as np
from PIL import Image
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN အဆင်မပြေပါ။")

# OCR Reader ကို စတင် အသက်သွင်းခြင်း (စာလုံးအပြည့်အစုံဖတ်နိုင်ရန်)
reader = easyocr.Reader(['en'], gpu=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်တို့၏ PPG Post ကို Group/Channel များတွင် Share ထားသော Screenshot ပုံကို ပို့ပေးပါ။ စစ်ဆေးပေးပါမည်။"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ထဲရှိ စာသားများကို အတိအကျ စစ်ဆေးနေပါသည်...")
    
    try:
        # Telegram မှ ပုံကို ရယူခြင်း
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # PIL Image သို့ ပြောင်းလဲခြင်း
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        # EasyOCR ဖြင့် ပုံထဲရှိ စာလုံးအားလုံးကို ဖတ်ယူခြင်း
        ocr_results = reader.readtext(image_np, detail=0)
        full_text = " ".join(ocr_results).upper()
        
        logging.info(f"Detected Text: {full_text}")
        
        # 'PPG' သို့မဟုတ် 'PPG ADS' စာတန်း ပါမပါ တိုက်ရိုက် စစ်ဆေးခြင်း
        if "PPG" in full_text or "PPG ADS" in full_text:
            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                "🎁 သင်တောင်းဆိုထားသော Link/Content ဖြစ်ပါတယ် -\n"
                "https://t.me/+8XdZgmVwrvwyZGVl"
            )
        else:
            await status_msg.edit_text(
                "❌ PPG Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG' သို့မဟုတ် 'Forwarded from PPG' စာတန်း အပြည့်အစုံပါသော ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        await status_msg.edit_text("❌ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။ ပုံကို ပြန်လည် ပို့ပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running with OCR setup...")
    app.run_polling()
