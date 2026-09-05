import os
import logging
import threading
import time
import requests
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes


# Flask-приложение для ответа на пинги
app = Flask(__name__)



TOKEN = os.environ.get("BOT_TOKEN")

# Ссылки на ваши приложения (замените на свои)
APP_SLOVARNIK = "https://obr-i.github.io/vocab/"          # словарные слова
APP_ORFOEPIA = "https://obr-i.github.io/orthoepy_cards/"  # орфоэпия

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаём две кнопки
    keyboard = [
        [
            InlineKeyboardButton(
                text="📚 Словарные слова",
                web_app=WebAppInfo(url=APP_SLOVARNIK)
            )
        ],
        [
            InlineKeyboardButton(
                text="🔊 Орфоэпия (ударения)",
                web_app=WebAppInfo(url=APP_ORFOEPIA)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Выбери тренажёр:",
        reply_markup=reply_markup
    )

# ---- Flask-маршрут для проверки жизни ----
@app.route('/')
def index():
    return "Бот работает!", 200

@app.route('/ping')
def ping():
    return "pong", 200

# ---- Функция self-ping (запускается в отдельном потоке) ----
def self_pinger():
    # Получаем URL сервера из переменной окружения RENDER_EXTERNAL_URL или используем локальный
    # На Render после деплоя будет доступна переменная RENDER_EXTERNAL_URL, но можно и руками указать
    host = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000")
    ping_url = f"{host}/ping"
    while True:
        try:
            requests.get(ping_url, timeout=5)
            logging.info(f"Self-ping успешен: {ping_url}")
        except Exception as e:
            logging.warning(f"Self-ping не удался: {e}")
        # Пауза 14 минут (840 секунд) — меньше, чем таймаут Render (15 минут)
        time.sleep(840)

# ---- Главная функция ----
def main():
    # Запускаем self-pinger в фоновом потоке
    pinger_thread = threading.Thread(target=self_pinger, daemon=True)
    pinger_thread.start()

    # Запускаем Flask-сервер в отдельном потоке (чтобы не блокировать основной)
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': int(os.environ.get('PORT', 5000)), 'debug': False}, daemon=True)
    flask_thread.start()

    # Запускаем Telegram бота (основной поток)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
