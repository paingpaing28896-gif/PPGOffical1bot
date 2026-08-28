import os
import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_CHAT_ID = "-1003790274194" # စစ်ဆေးတွေ့ရှိသော Channel ID မှန်

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN မရှိပါ။")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! PPG Post ကို Share ထားသော Screenshot ပုံ ပို့ပေးပါ။"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("စစ်ဆေးနေပါသည်...")
    
    try:
        # မိနစ် ၂၀ သက်တမ်းရှိပြီး ၁ ယောက်ပဲ သုံးလို့ရမည့် Link ထုတ်ပေးခြင်း
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
            
    except Exception as e:
        logging.error(f"Error creating invite link: {e}")
        await status_msg.edit_text(f"❌ Error ဖြစ်ပေါ်နေပါသည်: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running successfully...")
    app.run_polling()
