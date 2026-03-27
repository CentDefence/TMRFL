import asyncio
import aiosqlite
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command

TOKEN = "8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA"
ADMINS = [8214590613]

bot = Bot(TOKEN)
dp = Dispatcher()

cooldown = {}
user_data = {}

# ---------- DB ----------
async def init_db():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, nick TEXT)")
        await db.commit()

async def verified(uid):
    async with aiosqlite.connect("db.sqlite") as db:
        cur = await db.execute("SELECT * FROM users WHERE id=?", (uid,))
        return await cur.fetchone()

# ---------- ANTISPAM ----------
def check(uid):
    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 30:
        return False
    cooldown[uid] = now
    return True

# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(f"""👋 Привет, {msg.from_user.first_name}

🎮 Трансфер Маркет RFL

📌 t.me/RFLtransferMarket

📋 Команды:
/verify
/announce
/report
/transfer
/partnership
/setpartnership
""")

# ---------- VERIFY ----------
@dp.message(Command("verify"))
async def verify(msg: Message):
    if await verified(msg.from_user.id):
        return await msg.answer("✅ Уже верифицирован")

    await msg.answer("📝 Введи Roblox ник:")

    @dp.message()
    async def save(m: Message):
        async with aiosqlite.connect("db.sqlite") as db:
            await db.execute("INSERT INTO users VALUES (?,?)", (m.from_user.id, m.text))
            await db.commit()
        await m.answer("✅ Готово!")
        dp.message.unregister(save)

# ---------- ANNOUNCE ----------
@dp.message(Command("announce"))
async def announce(msg: Message):
    if not await verified(msg.from_user.id):
        return await msg.answer("❗ /verify сначала")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free Agent", callback_data="fa")],
        [InlineKeyboardButton(text="🏆 Лига", callback_data="league")],
        [InlineKeyboardButton(text="🏟 Клуб", callback_data="club")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await msg.answer("📢 Выбери тип:", reply_markup=kb)

# ---------- POSITIONS ----------
positions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="GK", callback_data="p_GK"),
     InlineKeyboardButton(text="CB", callback_data="p_CB"),
     InlineKeyboardButton(text="CM", callback_data="p_CM")],
    [InlineKeyboardButton(text="LW", callback_data="p_LW"),
     InlineKeyboardButton(text="RW", callback_data="p_RW"),
     InlineKeyboardButton(text="p_ST", callback_data="p_ST")]
])

@dp.callback_query(F.data == "fa")
async def fa(call: CallbackQuery):
    await call.message.answer("📌 Выбери позицию:", reply_markup=positions)

@dp.callback_query(F.data.startswith("p_"))
async def pos(call: CallbackQuery):
    user_data[call.from_user.id] = {"pos": call.data.split("_")[1]}
    await call.message.answer("✏️ Напиши о себе:")

    @dp.message()
    async def finish(m: Message):
        if not check(m.from_user.id):
            return await m.answer("⏳ Подожди")

        pos = user_data[m.from_user.id]["pos"]

        text = f"""📢 СВОБОДНЫЙ АГЕНТ

💠 @{m.from_user.username}
⚽ {pos}

📝 {m.text}

#FreeAgent #TMRFL"""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅", callback_data=f"ok_{m.from_user.id}")],
            [InlineKeyboardButton(text="❌", callback_data=f"no_{m.from_user.id}")]
        ])

        for admin in ADMINS:
            await bot.send_message(admin, text, reply_markup=kb)

        await m.answer("⏳ Отправлено")
        dp.message.unregister(finish)

# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠ Лига", callback_data="r1")],
        [InlineKeyboardButton(text="⚠ Игрок", callback_data="r2"),
         InlineKeyboardButton(text="⚠ Клуб", callback_data="r3")]
    ])
    await msg.answer("🚨 Выбери:", reply_markup=kb)

@dp.callback_query(F.data.startswith("r"))
async def rep(call: CallbackQuery):
    await call.message.answer("✏️ Опиши жалобу:")

    @dp.message()
    async def send(m: Message):
        text = f"""🚨 BlackList ALERT

👤 @{m.from_user.username}
📌 {m.text}"""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅", callback_data=f"ok_{m.from_user.id}")],
            [InlineKeyboardButton(text="❌", callback_data=f"no_{m.from_user.id}")]
        ])

        for admin in ADMINS:
            await bot.send_message(admin, text, reply_markup=kb)

        await m.answer("⏳ Отправлено")
        dp.message.unregister(send)

# ---------- TRANSFER ----------
@dp.message(Command("transfer"))
async def transfer(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Переход", callback_data="t1")]
    ])
    await msg.answer("Выбери:", reply_markup=kb)

@dp.callback_query(F.data == "t1")
async def t(call: CallbackQuery):
    await call.message.answer("✏️ Напиши переход:")

    @dp.message()
    async def send(m: Message):
        text = f"""❗️📢 ПЕРЕХОД

💠 {m.text}
👤 @{m.from_user.username}"""

        for admin in ADMINS:
            await bot.send_message(admin, text)

        await m.answer("⏳ Отправлено")
        dp.message.unregister(send)

# ---------- PARTNERSHIP ----------
@dp.message(Command("partnership"))
async def part(msg: Message):
    await msg.answer("""🤝 Партнерство:

🏆 Лиги
📰 Новостники
🏟 Клубы

Чтобы стать партнером:
/setpartnership""")

@dp.message(Command("setpartnership"))
async def setpart(msg: Message):
    await msg.answer("✏️ Отправь ссылку и описание:")

    @dp.message()
    async def send(m: Message):
        text = f"""🤝 ПАРТНЕРСТВО

👤 @{m.from_user.username}
📌 {m.text}"""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅", callback_data=f"ok_{m.from_user.id}")],
            [InlineKeyboardButton(text="❌", callback_data=f"no_{m.from_user.id}")]
        ])

        for admin in ADMINS:
            await bot.send_message(admin, text, reply_markup=kb)

        await m.answer("⏳ Отправлено")
        dp.message.unregister(send)

# ---------- ACCEPT ----------
@dp.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "✅ Принято!")

    await call.message.edit_text("✅ Опубликовано")

@dp.callback_query(F.data.startswith("no_"))
async def no(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "❌ Отклонено")
    await call.message.edit_text("❌ Отклонено")

# ---------- RUN ----------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())