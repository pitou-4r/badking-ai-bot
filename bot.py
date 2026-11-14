import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. ទាញយក API Keys ពី Environment Variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. កំណត់ដំណើរការ Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

user_chats = {}

# 3. បង្កើត Web Server ខ្នាតតូចសម្រាប់ Render Port Binding
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram AI Bot is running smoothly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 4. មុខងារ Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("សួស្តី! ខ្ញុំជា AI Bot របស់អ្នក។ សួរអ្វីមកខ្ញុំក៏បានដែរ!")

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("បានសម្អាតការចងចាំចាស់ៗរួចរាល់ហើយ!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = user_chats[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"សុំទោស មានបញ្ហាបច្ចេកទេស៖ {str(e)}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Error: ខ្វះ Environment Variables!")
        exit(1)

    threading.Thread(target=run_web, daemon=True).start()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_memory))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot កំពុងដំណើរការ...")
    application.run_polling()
