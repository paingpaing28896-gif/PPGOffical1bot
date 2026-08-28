import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Forward လုပ်လိုက်သော Channel သို့မဟုတ် Message ၏ Chat ID ကို ပြသပေးမည်
    if update.message.forward_from_chat:
        chat_id = update.message.forward_from_chat.id
        title = update.message.forward_from_chat.title
        await update.message.reply_text(f"📌 Channel Name: {title}\n🆔 Channel ID: `{chat_id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("ကျေးဇူးပြု၍ သင့် Channel ထဲမှ Post တစ်ခုခုကို ဒီ Bot ဆီသို့ Forward ပို့ပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, get_id))
    print("ID Finder Bot running...")
    app.run_polling()
