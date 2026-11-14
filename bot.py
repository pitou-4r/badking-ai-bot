import os
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. ទាញយក API Keys ពី Environment Variables របស់ Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. កំណត់ដំណើរការ Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') # លឿន និងឆ្លាត

# រក្សាទុកប្រវត្តិសន្ទនាសម្រាប់ User ម្នាក់ៗ (Memory)
user_chats = {}

# 3. បង្កើត Web Server ខ្នាតតូចសម្រាប់បំពេញលក្ខខណ្ឌ Port របស់ Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram AI Bot is running smoothly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 4. មុខងាររបស់ Telegram Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("សួស្តី! ខ្ញុំជា AI Bot របស់អ្នក។ សួរអ្វីមកខ្ញុំក៏បានដែរ!")

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("បានសម្អាតការចងចាំចាស់ៗរួចរាល់ហើយ! ចាប់ផ្តើមនិយាយរឿងថ្មីបាន។")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # បង្កើត Chat session ថ្មីបើមិនទាន់មាន
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    # បង្ហាញសញ្ញា "typing..." លើ Telegram
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = user_chats[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"សុំទោស មានបញ្ហាបច្ចេកទេសបន្តិច៖ {str(e)}")

# 5. ចាប់ផ្តើមដំណើរការទាំង Web Server និង Bot ព្រមគ្នា
if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Error: សូមពិនិត្យមើល TELEGRAM_TOKEN និង GEMINI_API_KEY ក្នុង Environment Variables!")
        exit(1)

    # បើក Flask Web Server ក្នុង Thread ផ្សេង
    threading.Thread(target=run_web, daemon=True).start()

    # បើកដំណើរការ Telegram Bot
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_memory))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot កំពុងដំណើរការ...")
    application.run_polling()
