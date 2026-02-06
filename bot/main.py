import asyncio
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from dotenv import load_dotenv

# 🔑 Загружаем переменные из .env
load_dotenv()

# Получаем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Токен не найден! Создайте файл .env с BOT_TOKEN=...")

# Остальные настройки
PLAYERS_FILE = os.path.join(os.path.dirname(__file__), "players.json")
WEBAPP_URL = "http://localhost:8000"  # потом заменишь

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_players():
    if os.path.exists(PLAYERS_FILE):
        try:
            with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_players(players):
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

def create_player():
    return {
        "rating": 0,
        "ton_balance": 0.0,
        "deck": {},
        "battles_used": 0,
        "extra_battles": 0
    }

@dp.message(Command("start"))
async def send_welcome(message: Message):
    players = load_players()
    user_id = str(message.from_user.id)
    
    if user_id not in players:
        players[user_id] = create_player()
        save_players(players)
        await message.answer("🆕 Добро пожаловать!")
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Рейтинг"),
                KeyboardButton(text="💰 Баланс"),
                KeyboardButton(text="🎮 Играть", web_app=WebAppInfo(url=WEBAPP_URL))
            ]
        ],
        resize_keyboard=True
    )
    await message.answer("Главное меню:", reply_markup=kb)

@dp.message(lambda msg: msg.text == "📊 Рейтинг")
async def show_rating(message: Message):
    players = load_players()
    user_id = str(message.from_user.id)
    rating = players.get(user_id, {}).get("rating", 0)
    await message.answer(f"🏅 Рейтинг: {rating}")

@dp.message(lambda msg: msg.text == "💰 Баланс")
async def show_balance(message: Message):
    players = load_players()
    user_id = str(message.from_user.id)
    balance = players.get(user_id, {}).get("ton_balance", 0.0)
    await message.answer(f"💰 Баланс: {balance:.2f} TON")

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())