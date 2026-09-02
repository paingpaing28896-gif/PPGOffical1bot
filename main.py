import os
import time
import requests
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- API Keys ---
TELEGRAM_TOKEN = "8621496121:AAHx3Bxo9t20ZMHFZ1BfrzDt0cxkMFweTPk"
OCR_SPACE_API_KEY = "K85121949688957"
CHANNEL_CHAT_ID = "-1004317280519"

# Web Server (Glitch 24/7 Run ရန်)
app = Flask('')

@app.route('/')
def home():
    return "Bot is active!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))

# Telegram Bot Logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! PPG Post ကို Share ထားသော Screenshot ပုံ ပို့ပေးပါ။")

def get_ocr_text(file_path):
    # Engine 1 & 2 ဖြင့် Fail-safe စစ်ပေးခြင်း
    for engine in [1, 2]:
        try:
            with open(file_path, 'rb') as f:
                res = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'filename': f},
                    data={'apikey': OCR_SPACE_API_KEY, 'language': 'eng', 'OCREngine': engine},
                    timeout=10
                )
            if res.status_code == 200:
                data = res.json()
                if data.get("ParsedResults"):
                    return data["ParsedResults"][0].get("ParsedText", "").upper()
        except:
            continue
    return ""

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🔍 ပုံထဲမှ စာသားကို စစ်ဆေးနေပါသည်...")
    file_path = f"temp_{update.message.from_user.id}.jpg"
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(file_path)

        extracted_text = get_ocr_text(file_path)

        if os.path.exists(file_path):
            os.remove(file_path)

        if "PPG" in extracted_text:
            expire_timestamp = int(time.time()) + 1200
            single_use_link = await context.bot.create_chat_invite_link(
                chat_id=CHANNEL_CHAT_ID, member_limit=1, expire_date=expire_timestamp
            )
            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                f"🎁 Link: {single_use_link.invite_link}\n\n"
                "⚠️ *ဤ Link သည် မိနစ် (၂၀) အတွင်း ၁ ကြိမ်သာ သုံးခွင့်ရှိပါသည်။*",
                parse_mode="Markdown"
            )
        elif extracted_text == "":
            await status_msg.edit_text("❌ စာသားဖတ်သည့် Server ခဏတာ မအားပါ။ ကျေးဇူးပြု၍ ခဏစောင့်ပြီး ပုံကို ပြန်ပို့ပေးပါ။")
        else:
            await status_msg.edit_text("❌ ပုံထဲတွင် PPG Ads စာသားကို မတွေ့ရှိပါ။ PPG Share ထားသည့် ပုံကို ပြန်ပို့ပေးပါ။")
            
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.edit_text(f"❌ Error ဖြစ်ပေါ်နေပါသည်: {e}")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    bot_app.run_polling()
