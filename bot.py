# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import os
import requests
import threading
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# تنظیمات لاگ برای اشکال‌زدایی
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = Flask(__name__)

# اطلاعات موردنیاز
TELEGRAM_BOT_TOKEN = "7997583221:AAGlMe6GaDl3l9zwcVVxRiUdkOFQZncXWW8"
SERVER_URL = "https://xcoore-development.glitch.me/"
user_data = {}

@app.route('/receive_data', methods=['POST'])
def receive_data():
    """دریافت اطلاعات از کلاینت و ورود به سایت کارسنج"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Missing username or password'}), 400

    result = login_to_karsanj(username, password)
    return jsonify({'status': 'success', 'message': result})

def login_to_karsanj(username, password):
    """ورود به حساب کاربری در کارسنج و دریافت اطلاعات"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get("https://karsanj.net")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="form"]/input'))).click()

        if "Invalid username or password" in driver.page_source:
            driver.quit()
            return "Login failed: Invalid credentials."

        driver.get("https://karsanj.net/student_panel.php")
        driver.quit()
        return "Login successful, data processed."

    except Exception as e:
        return f"Error: {str(e)}"

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
                await update.message.reply_text(f"⚠️ Problem while sending the message. Error code:: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logging.error(f"🚨 Error with connecting to the server: {str(e)}")
            await update.message.reply_text("🚨 Error with connecting to the server.")
    else:
        await update.message.reply_text("❌ Incomplete data.")

def run_flask():
    """اجرای سرور Flask در یک ترد جداگانه"""
    app.run(host='0.0.0.0', port=5000)

def main():
    """اجرای بات تلگرام در ترد اصلی و Flask در ترد جداگانه"""
    # اجرای سرور Flask در ترد جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # اجرای بات تلگرام در ترد اصلی
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("🤖 Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()

