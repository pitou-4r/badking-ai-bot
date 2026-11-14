import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. ទាញយក API Keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # ប្រើប្រាស់ gemini-2.5-flash ដើម្បីធានាដំណើរការរលូន ១០០%
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

user_chats = {}

# 2. បង្កើត Flask App
app = Flask(__name__)

# កសាង Telegram Application ជា Global
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if model:
        user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("សួស្តី! ខ្ញុំជា AI Bot របស់អ្នក។ សួរអ្វីមកខ្ញុំក៏បានដែរ!")

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if model:
        user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("បានសម្អាតការចងចាំចាស់ៗរួចរាល់ហើយ!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if not model:
        await update.message.reply_text("សូមកំណត់ GEMINI_API_KEY ជាមុនសិន!")
        return

    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = user_chats[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"សុំទោស មានបញ្ហាបច្ចេកទេស៖ {str(e)}")

# Add Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("clear", clear_memory))
telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

@app.route('/')
def home():
    return "Telegram AI Bot is running!"

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    async def process():
        async with telegram_app:
            await telegram_app.process_update(update)
    import asyncio
    asyncio.run(process())
    return "OK", 200

if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 8080))
    URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if URL:
        import requests
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={URL}/{TELEGRAM_TOKEN}")

    app.run(host="0.0.0.0", port=PORT)
