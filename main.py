import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA")
ADMINS = [8214590613]

bot = Bot(TOKEN)
dp = Dispatcher()

# ---------------- STATES ----------------
class Form(StatesGroup):
    verify = State()
    fa_pos = State()
    fa_text = State()
    league = State()
    club = State()
    report = State()
    transfer = State()
    partner_type = State()
    partner_info = State()

# ---------------- DB ----------------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, roblox TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS partners (type TEXT, link TEXT, info TEXT)")
        await db.commit()

async def is_verified(uid):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT * FROM users WHERE id=?", (uid,)) as c:
            return await c.fetchone()

async def add_user(uid, name):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT INTO users VALUES (?, ?)", (uid, name))
        await db.commit()

async def add_partner(type_, link, info):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT INTO partners VALUES (?, ?, ?)", (type_, link, info))
        await db.commit()

async def get_partners(type_):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT link, info FROM partners WHERE type=?", (type_,)) as c:
            return await c.fetchall()

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(msg: Message):
    text = f"""
👋 Привет, {msg.from_user.first_name}!
🎮 <b>Трансфер Маркет RFL</b>

Здесь можно создавать объявления Free Agent, набор в лигу/клуб, жалобы, партнерства и многое другое!

📌 <a href="https://t.me/RFLtransferMarket">Ссылка на канал</a>

📋 <b>Список команд:</b>
/verify - пройти верификацию
/announce - создать объявление
/report - пожаловаться
/transfer - переход игрока
/partnership - список партнеров
/setpartnership - стать партнером
"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Перейти в канал", url="https://t.me/RFLtransferMarket")]
    ])
    await msg.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=False)

# ---------------- VERIFY ----------------
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    if await is_verified(msg.from_user.id):
        return await msg.answer("✅ Вы уже прошли Verify!")
    await msg.answer("🛡 Введите Roblox ник:")
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Готово! Теперь доступны все команды.")
    await state.clear()

# ---------------- ANNOUNCE ----------------
@dp.message(Command("announce"))
async def announce(msg: Message):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🆓 Free Agent", callback_data="fa")],
        [InlineKeyboardButton("🏆 Лига", callback_data="league")],
        [InlineKeyboardButton("🏟 Клуб", callback_data="club")]
    ])
    await msg.answer("📢 Выберите тип:", reply_markup=kb)

# FA позиции
@dp.callback_query(F.data == "fa")
async def fa(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(p, callback_data=f"pos_{p}") for p in ["GK","CB","CM"]],
        [InlineKeyboardButton(p, callback_data=f"pos_{p}") for p in ["LW","RW","ST"]],
        [InlineKeyboardButton("ALL ROUNDER", callback_data="pos_ALL")]
    ])
    await cb.message.answer("Выберите позицию:", reply_markup=kb)

@dp.callback_query(F.data.startswith("pos_"))
async def fa_pos(cb: CallbackQuery, state: FSMContext):
    await state.update_data(pos=cb.data.split("_")[1])
    await cb.message.answer("✏️ Напишите о себе:\nПример: Игрок @Sqvnix, играю ST, опыт 2 года")
    await state.set_state(Form.fa_text)

@dp.message(Form.fa_text)
async def fa_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    text = f"""📢 СВОБОДНЫЙ АГЕНТ

💠 @{msg.from_user.username}
-- Позиция: {data['pos']}
-- О себе: {msg.text}

#FreeAgent"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅", callback_data=f"fa_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌", callback_data=f"fa_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb)
    await msg.answer("📨 Отправлено!")
    await state.clear()

# ---------------- TRANSFER ----------------
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала /verify")
    await msg.answer(
        "📢 Скопируйте и заполните:\n\n"
        "💠 @username - клуб с которого вы перешли ➡ клуб в который вы перешли"
    )
    await state.set_state(Form.transfer)

@dp.message(Form.transfer)
async def transfer_send(msg: Message):
    if "➡" not in msg.text or "-" not in msg.text:
        return await msg.answer("❌ Используйте шаблон!")
    for a in ADMINS:
        await bot.send_message(a, f"📢 ПЕРЕХОД\n{msg.text}")
    await msg.answer("✅ Отправлено!")

# ---------------- REPORT ----------------
@dp.message(Command("report"))
async def report(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Игрок", callback_data="r_player")],
        [InlineKeyboardButton("Клуб", callback_data="r_club")],
        [InlineKeyboardButton("Лига", callback_data="r_league")]
    ])
    await msg.answer("Выберите тип жалобы:", reply_markup=kb)

@dp.callback_query(F.data.startswith("r_"))
async def report_type(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.report)
    await cb.message.answer("Напишите жалобу:\nПример: Ник, причина, срок")

@dp.message(Form.report)
async def report_send(msg: Message):
    for a in ADMINS:
        await bot.send_message(a, f"🚨 Жалоба\n@{msg.from_user.username}\n{msg.text}")
    await msg.answer("📨 Жалоба отправлена")

# ---------------- SET PARTNERSHIP ----------------
@dp.message(Command("setpartnership"))
async def set_partner(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Лига", callback_data="p_league")],
        [InlineKeyboardButton("Клуб", callback_data="p_club")],
        [InlineKeyboardButton("Новостник", callback_data="p_news")]
    ])
    await msg.answer("Выберите тип:", reply_markup=kb)

@dp.callback_query(F.data.startswith("p_"))
async def partner_type(cb: CallbackQuery, state: FSMContext):
    t = cb.data.split("_")[1]
    await state.update_data(type=t)
    await cb.message.answer("Отправьте ссылку + описание")
    await state.set_state(Form.partner_info)

@dp.message(Form.partner_info)
async def partner_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅", callback_data=f"p_ok|{data['type']}|{msg.text}")],
        [InlineKeyboardButton("❌", callback_data="p_no")]
    ])
    for a in ADMINS:
        await bot.send_message(a, f"🤝 Партнерство\n{msg.text}", reply_markup=kb)
    await msg.answer("📨 Отправлено!")
    await state.clear()

@dp.callback_query(F.data.startswith("p_ok"))
async def p_ok(cb: CallbackQuery):
    _, type_, text = cb.data.split("|",2)
    await add_partner(type_, text, "")
    await cb.answer("Добавлено")

# ---------------- PARTNERSHIP LIST ----------------
@dp.message(Command("partnership"))
async def partner_list(msg: Message):
    text = "📜 Партнеры:\n\n"
    for t in ["league","club","news"]:
        data = await get_partners(t)
        if data:
            text += f"\n{t.upper()}:\n"
            for link,info in data:
                text += f"• {link}\n"
    await msg.answer(text)

# ---------------- RUN ----------------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())