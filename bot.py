import asyncio
import os
import time
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA")  # Вставь токен сюда
ADMINS = [8214590613]  # ID админов

bot = Bot(TOKEN)
dp = Dispatcher()

COOLDOWN = 10
cooldowns = {}
def anti_spam(user_id):
    now = time.time()
    if user_id in cooldowns and now - cooldowns[user_id] < COOLDOWN:
        return False
    cooldowns[user_id] = now
    return True

# -------- STATES --------
class Form(StatesGroup):
    verify = State()
    announce_fa = State()
    announce_league = State()
    announce_club = State()
    report = State()
    partnership = State()
    set_partnership = State()
    transfer_info = State()

# -------- DATABASE --------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            roblox TEXT
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            info TEXT
        )""")
        await db.commit()

async def add_user(user_id, roblox):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, roblox))
        await db.commit()

async def is_verified(uid):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT roblox FROM users WHERE user_id=?", (uid,)) as c:
            return await c.fetchone()

# -------- BACK BUTTON --------
BACK_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
])

@dp.callback_query(F.data == "back_start")
async def back_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    text = f"""👋 Привет, {cb.from_user.full_name}!
🎮 *Трансфер Маркет RFL*

Здесь можно создавать объявления Free Agent, набор в лигу/клуб, жалобы, партнерства и многое другое!

📌 Ссылка: [t.me/RFLtransferMarket](https://t.me/RFLtransferMarket)

📋 *Список команд:*
/verify - пройти верификацию
/announce - создать объявление
/report - пожаловаться
/transfer - переход игрока
/partnership - сотрудничество
/setpartnership - стать партнером"""
    await cb.message.edit_text(text, parse_mode="Markdown")
    await cb.answer()

# -------- START --------
@dp.message(Command("start"))
async def start(msg: Message):
    await back_start(CallbackQuery(message=msg, from_user=msg.from_user, data=""), FSMContext(dp))

# -------- VERIFY --------
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    await msg.answer("🛡 Введите ваш Roblox ник для использования команд. ⚠️ Ник можно менять только через ЛС владельца.")
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Верификация пройдена! Теперь доступны все команды.", reply_markup=BACK_KB)
    await state.clear()

# -------- ANNOUNCE --------
@dp.message(Command("announce"))
async def announce(msg: Message):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🆓 Free Agent", callback_data="announce_fa")],
        [InlineKeyboardButton("🏆 Набор в Лигу", callback_data="announce_league")],
        [InlineKeyboardButton("🏟 Набор в Клуб", callback_data="announce_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип объявления:", reply_markup=kb)

# -- Free Agent --
@dp.callback_query(F.data == "announce_fa")
async def announce_fa_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("📝 Напишите свои позиции и немного о себе:", reply_markup=BACK_KB)
    await state.set_state(Form.announce_fa)

@dp.message(Form.announce_fa)
async def announce_fa_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    text = f"""📢 *СВОБОДНЫЙ АГЕНТ*
💠 @{msg.from_user.username} - Ищет клуб
-- Позиции/о себе: {msg.text}
#FreeAgent #TMRFL"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"fa_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"fa_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваше объявление отправлено на модерацию!", reply_markup=BACK_KB)
    await state.clear()

# -- League --
@dp.callback_query(F.data == "announce_league")
async def announce_league_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("📄 Введите ссылку на лигу, количество мест, занято, описание:", reply_markup=BACK_KB)
    await state.set_state(Form.announce_league)

@dp.message(Form.announce_league)
async def announce_league_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    text = f"""📢 *НАБОР В ЛИГУ*
💠 @{msg.from_user.username}
-- Информация: {msg.text}
#LeagueAnnounce #TMRFL"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"league_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"league_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваше объявление отправлено на модерацию!", reply_markup=BACK_KB)
    await state.clear()

# -- Club --
@dp.callback_query(F.data == "announce_club")
async def announce_club_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("🏟 Введите название клуба и информацию о наборе:", reply_markup=BACK_KB)
    await state.set_state(Form.announce_club)

@dp.message(Form.announce_club)
async def announce_club_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    text = f"""📢 *НАБОР В КЛУБ*
💠 Владелец: @{msg.from_user.username}
-- Информация: {msg.text}
#LeagueAnnounce #TMRFL"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"club_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"club_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваше объявление отправлено на модерацию!", reply_markup=BACK_KB)
    await state.clear()

# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(msg: Message):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⚠️ Жалоба на Лигу", callback_data="report_league")],
        [InlineKeyboardButton("⚠️ Жалоба на Игрока", callback_data="report_player")],
        [InlineKeyboardButton("⚠️ Жалоба на Клуб", callback_data="report_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип жалобы:", reply_markup=kb)

@dp.callback_query(F.data.startswith("report_"))
async def report_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("📝 Опишите жалобу подробно (ник, причина, срок):", reply_markup=BACK_KB)
    await state.set_state(Form.report)

@dp.message(Form.report)
async def report_send(msg: Message, state: FSMContext):
    text = f"""⚠️ *BLACKLIST ALERT*
💠 @{msg.from_user.username}
-- Жалоба: {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"report_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"report_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Жалоба отправлена на модерацию!", reply_markup=BACK_KB)
    await state.clear()

# ---------- PARTNERSHIP ----------
@dp.message(Command("partnership"))
async def partnership(msg: Message):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🤝 Лига", callback_data="partnership_league")],
        [InlineKeyboardButton("📰 Новостники", callback_data="partnership_news")],
        [InlineKeyboardButton("🏟 Клуб", callback_data="partnership_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип партнерства:", reply_markup=kb)

@dp.callback_query(F.data.startswith("partnership_"))
async def partnership_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("📄 Введите ссылку и информацию о сотрудничестве:", reply_markup=BACK_KB)
    await state.set_state(Form.partnership)

@dp.message(Form.partnership)
async def partnership_send(msg: Message, state: FSMContext):
    text = f"""🤝 *ПАРТНЕРСТВО*
💠 @{msg.from_user.username}
-- Информация: {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"partnership_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"partnership_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Заявка на партнерство отправлена!", reply_markup=BACK_KB)
    await state.clear()

# ---------- TRANSFER ----------
@dp.message(Command("transfer"))
async def transfer(msg: Message):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Переход в клуб", callback_data="transfer_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "transfer_club")
async def transfer_cb(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("📝 Укажите с какого клуба в какой перешли (пример: ClubA ➡ ClubB):", reply_markup=BACK_KB)
    await state.set_state(Form.transfer_info)

@dp.message(Form.transfer_info)
async def transfer_send(msg: Message, state: FSMContext):
    text = f"""❗️📢 *ПЕРЕХОД ОФИЦИАЛЬНО*
💠 @{msg.from_user.username}
-- Переход: {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"transfer_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"transfer_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Заявка на переход отправлена!", reply_markup=BACK_KB)
    await state.clear()

# ---------- ADMIN APPROVE/REJECT HANDLERS ----------
@dp.callback_query(F.data.endswith("_ok_") | F.data.endswith("_no_"))
async def admin_response(cb: CallbackQuery):
    action, _, uid_str = cb.data.split("_")
    uid = int(uid_str)
    if action == "fa" or action == "league" or action == "club" or action == "report" or action == "partnership" or action == "transfer":
        if cb.data.startswith(action+"_ok_"):
            await bot.send_message(uid, "✅ Ваша заявка успешно принята! О вас скоро напишут в канале.", reply_markup=BACK_KB)
        else:
            await bot.send_message(uid, "❌ Извиняемся! Ваша заявка не принята. Пожалуйста, не спамьте повторно. Если есть вопросы, напишите в тикет: t.me/TMRFLSUPPORT_bot", reply_markup=BACK_KB)
        await cb.answer("✅ Готово для админа")

# -------- RUN --------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())