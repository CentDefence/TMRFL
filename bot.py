import asyncio
import os
import time
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA")
ADMINS = [8214590613]

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()

# ---------- АНТИСПАМ ----------
cooldowns = {}
def anti_spam(uid):
    now = time.time()
    if uid in cooldowns and now - cooldowns[uid] < 5:
        return False
    cooldowns[uid] = now
    return True

# ---------- STATES ----------
class Form(StatesGroup):
    verify = State()
    fa_pos = State()
    fa_text = State()
    league = State()
    club = State()
    other = State()
    report_type = State()
    report_text = State()
    transfer = State()
    partner_type = State()
    partner_info = State()

# ---------- DB ----------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, roblox TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS bans (id INTEGER PRIMARY KEY)")
        await db.execute("CREATE TABLE IF NOT EXISTS partners (type TEXT, text TEXT)")
        await db.commit()

async def is_verified(uid):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT * FROM users WHERE id=?", (uid,)) as c:
            return await c.fetchone()

async def add_user(uid, name):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (uid, name))
        await db.commit()

async def is_banned(uid):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT * FROM bans WHERE id=?", (uid,)) as c:
            return await c.fetchone()

async def ban_user(uid):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO bans VALUES (?)", (uid,))
        await db.commit()

async def unban_user(uid):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("DELETE FROM bans WHERE id=?", (uid,))
        await db.commit()

async def add_partner(type_, text):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT INTO partners VALUES (?,?)", (type_, text))
        await db.commit()

async def get_partners(type_):
    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT text FROM partners WHERE type=?", (type_,)) as c:
            return await c.fetchall()

# ---------- UI ----------
def back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ])

def admin_kb(uid, tag):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"{tag}_ok_{uid}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"{tag}_no_{uid}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{uid}")]
    ])

# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(f"""
👋 <b>Привет, {msg.from_user.first_name}</b>
🎮 <b>Трансфер Маркет RFL</b>

Здесь можно делать объявления, жалобы, переходы и партнёрства!

📌 https://t.me/RFLtransferMarket

📋 <b>Команды:</b>
/verify
/announce
/report
/transfer
/setpartnership
/partnership
""")

# ---------- VERIFY ----------
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    if await is_verified(msg.from_user.id):
        return await msg.answer("✅ Уже есть verify")
    await msg.answer("Введите Roblox ник:")
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Готово", reply_markup=back())
    await state.clear()

# ---------- ANNOUNCE ----------
@dp.message(Command("announce"))
async def announce(msg: Message):
    if await is_banned(msg.from_user.id):
        return await msg.answer("🚫 Бан")
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ /verify")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🆓 Free Agent", callback_data="fa")],
        [InlineKeyboardButton("🏆 Лига", callback_data="league")],
        [InlineKeyboardButton("🏟 Клуб", callback_data="club")],
        [InlineKeyboardButton("📄 Другое", callback_data="other")]
    ])
    await msg.answer("Выбери:", reply_markup=kb)

# FA
@dp.callback_query(F.data == "fa")
async def fa(cb: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(p, callback_data=f"pos_{p}") for p in ["GK","CB","CM"]],
        [InlineKeyboardButton(p, callback_data=f"pos_{p}") for p in ["LW","RW","ST"]],
        [InlineKeyboardButton("ALL", callback_data="pos_ALL")]
    ])
    await cb.message.answer("Позиция:", reply_markup=kb)

@dp.callback_query(F.data.startswith("pos_"))
async def pos(cb: CallbackQuery, state: FSMContext):
    await state.update_data(pos=cb.data.split("_")[1])
    await cb.message.answer("Напиши о себе (пример: опыт, стиль игры)")
    await state.set_state(Form.fa_text)

@dp.message(Form.fa_text)
async def send_fa(msg: Message, state: FSMContext):
    data = await state.get_data()
    text = f"📢 FA\n@{msg.from_user.username}\n{data['pos']}\n{msg.text}"
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=admin_kb(msg.from_user.id,"fa"))
    await msg.answer("Отправлено", reply_markup=back())
    await state.clear()

# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Игрок", callback_data="r_player")],
        [InlineKeyboardButton("Клуб", callback_data="r_club")],
        [InlineKeyboardButton("Лига", callback_data="r_league")]
    ])
    await msg.answer("Тип жалобы:", reply_markup=kb)

@dp.callback_query(F.data.startswith("r_"))
async def r_type(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.report_text)
    await cb.message.answer("Опиши жалобу")

@dp.message(Form.report_text)
async def send_rep(msg: Message):
    for a in ADMINS:
        await bot.send_message(a, msg.text, reply_markup=admin_kb(msg.from_user.id,"rep"))
    await msg.answer("Отправлено")

# ---------- TRANSFER ----------
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    await msg.answer("Скопируй:\n💠 @user - клуб ➡ клуб")
    await state.set_state(Form.transfer)

@dp.message(Form.transfer)
async def send_tr(msg: Message):
    if "➡" not in msg.text:
        return await msg.answer("❌ шаблон")
    for a in ADMINS:
        await bot.send_message(a, msg.text, reply_markup=admin_kb(msg.from_user.id,"tr"))
    await msg.answer("Отправлено")

# ---------- PARTNERSHIP ----------
@dp.message(Command("setpartnership"))
async def setp(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Лига", callback_data="p_league")],
        [InlineKeyboardButton("Клуб", callback_data="p_club")],
        [InlineKeyboardButton("Новостник", callback_data="p_news")]
    ])
    await msg.answer("Тип:", reply_markup=kb)

@dp.callback_query(F.data.startswith("p_"))
async def ptype(cb: CallbackQuery, state: FSMContext):
    await state.update_data(type=cb.data.split("_")[1])
    await state.set_state(Form.partner_info)
    await cb.message.answer("Ссылка + описание")

@dp.message(Form.partner_info)
async def psend(msg: Message, state: FSMContext):
    data = await state.get_data()
    for a in ADMINS:
        await bot.send_message(a, msg.text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅", callback_data=f"p_ok_{data['type']}|{msg.text}")],
            [InlineKeyboardButton("❌", callback_data="p_no")]
        ]))
    await msg.answer("Отправлено")

@dp.callback_query(F.data.startswith("p_ok"))
async def pok(cb: CallbackQuery):
    _, rest = cb.data.split("_",1)
    t, text = rest.split("|",1)
    await add_partner(t,text)
    await cb.answer("Добавлено")

@dp.message(Command("partnership"))
async def plist(msg: Message):
    text = "Партнёры:\n"
    for t in ["league","club","news"]:
        data = await get_partners(t)
        if data:
            text += f"\n{t}:\n"
            for d in data:
                text += f"• {d[0]}\n"
    await msg.answer(text)

# ---------- ADMIN ----------
@dp.callback_query(F.data.startswith("ban_"))
async def ban(cb: CallbackQuery):
    uid = int(cb.data.split("_")[1])
    await ban_user(uid)
    await bot.send_message(uid, "🚫 Бан")
    await cb.answer()

@dp.message(Command("unban"))
async def unban(msg: Message):
    if msg.from_user.id not in ADMINS:
        return
    uid = int(msg.text.split()[1])
    await unban_user(uid)
    await msg.answer("Разбан")

# ---------- RUN ----------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())