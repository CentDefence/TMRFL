import asyncio
import time
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA"
ADMINS = [8214590613]

bot = Bot(TOKEN)
dp = Dispatcher()

# -------- АНТИ СПАМ --------
cooldowns = {}
COOLDOWN = 10

def anti_spam(user_id):
    now = time.time()
    if user_id in cooldowns and now - cooldowns[user_id] < COOLDOWN:
        return False
    cooldowns[user_id] = now
    return True

# -------- БД --------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            roblox TEXT
        )
        """)
        await db.commit()

async def add_user(user_id, roblox):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, roblox))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT roblox FROM users WHERE user_id=?", (user_id,)) as c:
            return await c.fetchone()

# -------- STATES --------
class Form(StatesGroup):
    verify = State()
    fa = State()
    league = State()
    club = State()
    report = State()
    transfer = State()
    partner = State()

# -------- МЕНЮ --------
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Объявление"), KeyboardButton(text="🚨 Жалоба")],
            [KeyboardButton(text="🤝 Партнёрство"), KeyboardButton(text="🔄 Трансфер")],
            [KeyboardButton(text="🛡 Verify")]
        ],
        resize_keyboard=True
    )

# -------- START --------
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(
        "👋 Привет! Это Трансфер Маркет RFL\n\n"
        "🔗 t.me/RFLtransferMarket\n\n"
        "👇 Используй меню ниже",
        reply_markup=main_menu()
    )

# -------- VERIFY --------
@dp.message(F.text == "🛡 Verify")
async def verify(msg: Message, state: FSMContext):
    await msg.answer("Введите Roblox ник:")
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Верификация пройдена!", reply_markup=main_menu())
    await state.clear()

async def is_verified(user_id):
    return await get_user(user_id)

# -------- ANNOUNCE --------
@dp.message(F.text == "📢 Объявление")
async def announce(msg: Message):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала Verify")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free Agent", callback_data="fa")],
        [InlineKeyboardButton(text="🏆 Лига", callback_data="league")],
        [InlineKeyboardButton(text="🏟 Клуб", callback_data="club")]
    ])
    await msg.answer("Выберите:", reply_markup=kb)

# ---- FREE AGENT ----
@dp.callback_query(F.data == "fa")
async def fa(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("Напишите позицию и о себе:")
    await state.set_state(Form.fa)

@dp.message(Form.fa)
async def fa_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подожди немного")

    text = f"""
📢 СВОБОДНЫЙ АГЕНТ

💠 @{msg.from_user.username}
-- {msg.text}

#FreeAgent #TMRFL
"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"ok_{msg.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{msg.from_user.id}")]
    ])

    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb)

    await msg.answer("📨 Отправлено")
    await state.clear()

# -------- REPORT --------
@dp.message(F.text == "🚨 Жалоба")
async def report(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Лига", callback_data="r1")],
        [InlineKeyboardButton(text="Игрок", callback_data="r2")],
        [InlineKeyboardButton(text="Клуб", callback_data="r3")]
    ])
    await msg.answer("Выбери тип:", reply_markup=kb)

# -------- TRANSFER --------
@dp.message(F.text == "🔄 Трансфер")
async def transfer(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Переход", callback_data="t1")]
    ])
    await msg.answer("Выбери:", reply_markup=kb)

@dp.callback_query(F.data == "t1")
async def t1(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(
        "❗️📢 ПЕРЕХОД\n\n"
        "ник - клуб ➡️ клуб"
    )
    await state.set_state(Form.transfer)

@dp.message(Form.transfer)
async def t_send(msg: Message, state: FSMContext):
    for a in ADMINS:
        await bot.send_message(a, msg.text + f"\n@{msg.from_user.username}")
    await msg.answer("✅ Отправлено")
    await state.clear()

# -------- ADMIN --------
@dp.callback_query(F.data.startswith("ok_"))
async def ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[1])
    await bot.send_message(uid, "✅ Принято")
    await cb.answer()

@dp.callback_query(F.data.startswith("no_"))
async def no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[1])
    await bot.send_message(uid, "❌ Отклонено")
    await cb.answer()

# -------- RUN --------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())