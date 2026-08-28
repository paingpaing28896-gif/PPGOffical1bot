import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Message ရဲ့ အချက်အလက်များမှ Channel ID ကို ရှာဖွေခြင်း
    origin = getattr(update.message, 'forward_origin', None)
    
    if origin and getattr(origin, 'type', None) == 'channel':
        chat_id = origin.chat.id
        title = origin.chat.title
        await update.message.reply_text(
            f"📌 **Channel Name:** {title}\n"
            f"🆔 **Channel ID:** `{chat_id}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("ကျေးဇူးပြု၍ သင့် Channel ထဲမှ Post တစ်ခုခုကို ဒီ Bot ဆီသို့ Forward ပြန်ပို့ပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, get_id))
    print("ID Finder Bot running...")
    app.run_polling()
