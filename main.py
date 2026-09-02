import os
import logging
import time
import requests
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ----------------- မိမိ API Key များ ထည့်ရန် -----------------
TELEGRAM_TOKEN = "8621496121:AAHx3Bxo9t20ZMHFZ1BfrzDt0cxkMFweTPk"
OCR_SPACE_API_KEY = "K85121949688957"
CHANNEL_CHAT_ID = "-1004317280519"
# -----------------------------------------------------------

# Glitch မအိပ်သွားစေရန် Web Server သေးသေးလေး ဆောက်ခြင်း
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running online!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Telegram Bot စစ်ဆေးသည့် Logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! PPG Post ကို Share ထားသော Screenshot ပုံ ပို့ပေးပါ။")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🔍 ပုံထဲမှ စာသားကို စစ်ဆေးနေပါသည်...")
    file_path = f"temp_{update.message.from_user.id}.jpg"
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(file_path)

        # OCR.space ဖြင့် စာသားစစ်ဆေးခြင်း
        with open(file_path, 'rb') as f:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'filename': f},
                data={'apikey': OCR_SPACE_API_KEY, 'language': 'eng', 'OCREngine': 2}
            )
        
        result = response.json()

        if os.path.exists(file_path):
            os.remove(file_path)

        extracted_text = ""
        if result.get("ParsedResults"):
            extracted_text = result["ParsedResults"][0].get("ParsedText", "").upper()

        # PPG စာသား ပါမပါ စစ်ဆေးခြင်း
        if "PPG" in extracted_text:
            expire_timestamp = int(time.time()) + 1200 # မိနစ် ၂၀ သက်တမ်း
            single_use_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_CHAT_ID, member_limit=1, expire_date=expire_timestamp
            )
            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                f"🎁 Link: {single_use_link.invite_link}\n\n"
                "⚠️ *ဤ Link သည် မိနစ် (၂၀) အတွင်း ၁ ကြိမ်သာ သုံးခွင့်ရှိပါသည်။*",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text("❌ ပုံထဲတွင် PPG Ads စာသားကို မတွေ့ရှိပါ။ PPG Share ထားသည့် ပုံကို ပြန်ပို့ပေးပါ။")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.edit_text(f"❌ Error ဖြစ်ပေါ်နေပါသည်: {e}")

if __name__ == '__main__':
    keep_alive() # Web Server စတင်မည်
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
