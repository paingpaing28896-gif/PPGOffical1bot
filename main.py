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

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("TELEGRAM_TOKEN သို့မဟုတ် GROQ_API_KEY အဆင်မပြေပါ။")

client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်ုပ်တို့၏ PPG Post ကို Group/Channel များတွင် Share ထားသော Screenshot ပုံကို ပို့ပေးပါ။ စစ်ဆေးပေးပါမည်။"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("Screenshot ကို အသေးစိတ် စစ်ဆေးနေပါသည်...")
    
    try:
        # Get highest resolution photo
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Convert image to Base64 format
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Groq LLaMA 3.2 Vision Model
        # System Prompt တွင် Explicit/NSFW content များကို ကျော်လွန်၍ Text/Header ကိုသာ စစ်ခိုင်းခြင်း
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Task: Verification. "
                                "Disregard any NSFW, adult, or sensitive visual content in the image. "
                                "Check ONLY if the screenshot shows a message or post forwarded/shared from 'PPG' or 'PPG Ads' "
                                "(look for 'Forwarded from PPG', 'PPG Ads', or 'PPG' text in headers or chat messages). "
                                "If the word 'PPG' exists in any text context, respond 'YES'. Otherwise, respond 'NO'."
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
            max_tokens=10,
            temperature=0.0
        )
        
        result = response.choices[0].message.content.strip()
        
        # AI ရဲ့ အဖြေအပေါ် မူတည်ပြီး တုံ့ပြန်ခြင်း
        if "YES" in result.upper():
            await status_msg.edit_text(
                "✅ စစ်ဆေးမှု အောင်မြင်ပါသည်။ PPG Post ကို ရှဲထားတာ မှန်ကန်ပါသည်။\n\n"
                "🎁 သင်တောင်းဆိုထားသော Link/Content ဖြစ်ပါတယ် -\n"
                "https://t.me/+8XdZgmVwrvwyZGVl"
            )
        else:
            await status_msg.edit_text(
                "❌ PPG Post ပါဝင်သော Screenshot မဟုတ်ပါ။ ကျေးဇူးပြု၍ 'PPG' သို့မဟုတ် 'Forwarded from PPG' စာတန်း ပါဝင်သော ပုံကို ပြန်လည် ပို့ပေးပါ။"
            )
            
    except Exception as e:
        logging.error(f"Error checking image: {e}")
        # Error ဖြစ်ခဲ့လျှင်သော်လည်းကောင်း Exception ထဲ ရောက်သွားပါက ပုံမှန်အတိုင်း တုံ့ပြန်ရန်
        await status_msg.edit_text(
            "❌ စစ်ဆေးမှု မအောင်မြင်ပါ။ PPG Post သို့မဟုတ် 'Forwarded from PPG' စာတန်း အပြည့်အစုံ ပါဝင်သော Screenshot ကို ပြန်လည် ပို့ပေးပါ။"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot is running...")
    app.run_polling()
