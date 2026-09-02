import os
import logging
import time
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Google AI Studio မှ API Key
CHANNEL_CHAT_ID = "-1003790274194"

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN သို့မဟုတ် GEMINI_API_KEY မရှိပါ။")

# Gemini AI ကို ပြင်ဆင်ခြင်း
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! PPG Post ကို Share ထားသော Screenshot ပုံ ပို့ပေးပါ။"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🔍 ပုံကို AI ဖြင့် စစ်ဆေးနေပါသည်...")
    file_path = f"temp_{update.message.from_user.id}.jpg"
    
    try:
        # ၁။ Telegram ထံမှ ပုံကို ဒေါင်းလုဒ်ဆွဲခြင်း
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(file_path)

        # ၂။ Gemini AI သို့ ပုံနှင့် Prompt ပို့၍ စစ်ဆေးခြင်း
        # နောက်ခံပုံကို လျစ်လျူရှုပြီး PPG Ads စာသား သီးသန့်ကိုပဲ စစ်ရန် AI ကို ညွှန်ကြားထားသည်
        sample_file = genai.upload_file(path=file_path)
        prompt = (
            "Analyze this image ONLY for text or branding logos. "
            "Ignore any background content, images, or graphics completely. "
            "Check if there is any text, watermark, or ad logo related to 'PPG' or 'PPG Ads' in any color or font style. "
            "Reply strictly with ONLY 'YES' if 'PPG' or 'PPG Ads' is present, or 'NO' if it is not present."
        )
        
        response = model.generate_content([sample_file, prompt])
        result_text = response.text.strip().upper()

        # ဒေါင်းလုဒ်ဆွဲထားသော ယာယီပုံအား ဖျက်ခြင်း
        if os.path.exists(file_path):
            os.remove(file_path)

        # ၃။ AI အဖြေပေါ်မူတည်၍ Link ထုတ်ပေးခြင်း
        if "YES" in result_text:
            expire_timestamp = int(time.time()) + 1200 # မိနစ် ၂၀ သက်တမ်း
            
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
                "❌ ပုံထဲတွင် PPG Ads စာသား သို့မဟုတ် Logo ကို မတွေ့ရှိပါ။\n"
                "ကျေးဇူးပြု၍ PPG Post အမှန်တကယ် Share ထားသည့် Screenshot ကို ပြန်လည်ပေးပို့ပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.edit_text(f"❌ Error ဖြစ်ပေါ်နေပါသည်: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running successfully...")
    app.run_polling()
