# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests
import logging

# تنظیمات لاگ برای اشکال‌زدایی
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# اطلاعات موردنیاز
TELEGRAM_BOT_TOKEN = "7997583221:AAGlMe6GaDl3l9zwcVVxRiUdkOFQZncXWW8"
SERVER_URL = "https://xcoore-development.glitch.me/"
user_data = {}

async def start(update: Update, context: CallbackContext):
    """شروع مکالمه و درخواست نام کاربری"""
    await update.message.reply_text("👋 Please enter your username.")
    user_data[update.effective_chat.id] = {"step": "username"}  

async def handle_message(update: Update, context: CallbackContext):
    """دریافت نام کاربری و رمز عبور"""
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in user_data:
        await update.message.reply_text("⛔ Please send /start first.")
        return

    user_step = user_data[chat_id].get("step")

    if user_step == "username":
        user_data[chat_id]["username"] = text
        user_data[chat_id]["step"] = "password"
        await update.message.reply_text("🔑 Please enter your password.")

    elif user_step == "password":
        user_data[chat_id]["password"] = text
        await send_data_to_server(chat_id, update)

async def send_data_to_server(chat_id, update):
    """ارسال اطلاعات به سرور Flask"""
    username = user_data[chat_id].get("username")
    password = user_data[chat_id].get("password")

    if username and password:
        data = {"username": username, "password": password}
        try:
            logging.info(f"📨 Sending Request to server: {data}")
            response = requests.post(f"{SERVER_URL}/receive_data", json=data)

            if response.status_code == 200:
                server_response = response.json()
                logging.info(f"✅ Server response: {server_response}")
                await update.message.reply_text(f"✅ Data sent successfully.\nServer response: {server_response}")
            else:
                logging.warning(f"⚠️ Error while sending: {response.status_code} - {response.text}")
                await update.message.reply_text(f"⚠️ Problem while sending the message. Error code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logging.error(f"🚨 Error with connecting to the server: {str(e)}")
            await update.message.reply_text("🚨 Error with connecting to the server.")
    else:
        await update.message.reply_text("❌ Incomplete data.")

def main():
    """اجرای بات تلگرام"""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
