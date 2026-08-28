import os
import logging
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render Environment Variables ထဲက Token နှင့် API Key များကို ဆွဲယူခြင်း
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("TELEGRAM_TOKEN သို့မဟုတ် GROQ_API_KEY အဆင်မပြေပါ။ Render Environment Variables ထဲမှာ ထည့်ပေးပါ။")

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်တို့၏ Channel ကို Group/Channel များတွင် Share ထားသော Screenshot ပုံကို ပို့ပေးပါ။ AI မှ စစ်ဆေးပေးပါမည်။"
    )

# Photo Handler (AI Screenshot Verification)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ကို AI မှ စစ်ဆေးနေပါသည်...")
    
    try:
        # Get highest resolution photo
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Convert image to Base64 format
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Groq Vision Model ဖြင့် စစ်ဆေးခြင်း
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot. Is it showing a shared post/message in a Telegram group or channel? "
                                "Answer strictly with 'YES' or 'NO'."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        
        # AI ရဲ့ အဖြေအပေါ် မူတည်ပြီး တုံ့ပြန်ခြင်း
        if "YES" in result.upper():
            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                "🎁 သင်တောင်းဆိုထားသော Link/Content ဖြစ်ပါတယ် -\n"
                "https://t.me/+8XdZgmVwrvwyZGVl"
            )
        else:
            await status_msg.edit_text(
                "❌ စစ်ဆေးမှု မအောင်မြင်ပါ။ ပို့ပေးသော Screenshot မှာ Share ထားသည့် ပုံစံမဟုတ်ပါ။ "
                "ကျေးဇူးပြု၍ ပြန်လည်စစ်ဆေးပြီး ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error checking image: {e}")
        await status_msg.edit_text("⚠️ စစ်ဆေးရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်နေပါသည်။ ခဏနေမှ ပြန်စမ်းပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running...")
    app.run_polling()
