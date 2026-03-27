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
user_state = {}
banned = set()

# ---------- DB ----------
async def init_db():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, nick TEXT)")
        await db.commit()

async def verified(uid):
    async with aiosqlite.connect("db.sqlite") as db:
        cur = await db.execute("SELECT * FROM users WHERE id=?", (uid,))
        return await cur.fetchone()

# ---------- АНТИСПАМ ----------
def check(uid):
    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 20:
        return False
    cooldown[uid] = now
    return True

def is_banned(uid):
    return uid in banned

# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(f"""👋 {msg.from_user.first_name}
🎮 TMRFL

/verify /announce
/report /transfer
/partnership /setpartnership""")

# ---------- VERIFY ----------
@dp.message(Command("verify"))
async def verify(msg: Message):
    if await verified(msg.from_user.id):
        return await msg.answer("✅ Уже есть")

    await msg.answer("📝 Введи Roblox ник")

    user_state[msg.from_user.id] = "verify"

@dp.message()
async def all_messages(msg: Message):
    uid = msg.from_user.id

    if is_banned(uid):
        return await msg.answer("🚫 Бан\nАпелляция: @sqvnix")

    if uid in user_state:

        # VERIFY
        if user_state[uid] == "verify":
            async with aiosqlite.connect("db.sqlite") as db:
                await db.execute("INSERT INTO users VALUES (?,?)", (uid, msg.text))
                await db.commit()
            user_state.pop(uid)
            return await msg.answer("✅ Готово\nТеперь доступ открыт")

        # FREE AGENT
        if user_state[uid] == "fa_text":
            if not check(uid):
                return await msg.answer("⏳ Подожди немного")

            pos = user_state[uid+"_pos"]

            text = f"""📢 FREE AGENT
@{msg.from_user.username} | {pos}"""

            desc = f"📝 {msg.text}\n#FA #TMRFL"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅", callback_data=f"ok_{uid}")],
                [InlineKeyboardButton(text="❌", callback_data=f"no_{uid}")],
                [InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{uid}")]
            ])

            for admin in ADMINS:
                await bot.send_message(admin, text+"\n"+desc, reply_markup=kb)

            user_state.pop(uid)
            return await msg.answer("⏳ Отправлено\nЖди проверки")

        # REPORT
        if user_state[uid] == "report":
            text = f"""🚨 REPORT
@{msg.from_user.username}"""

            desc = f"📌 {msg.text}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅", callback_data=f"ok_{uid}")],
                [InlineKeyboardButton(text="❌", callback_data=f"no_{uid}")],
                [InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{uid}")]
            ])

            for admin in ADMINS:
                await bot.send_message(admin, text+"\n"+desc, reply_markup=kb)

            user_state.pop(uid)
            return await msg.answer("⏳ Жалоба отправлена\nОжидай")

        # TRANSFER
        if user_state[uid] == "transfer":
            text = f"""📢 TRANSFER
@{msg.from_user.username}"""

            desc = f"➡️ {msg.text}"

            for admin in ADMINS:
                await bot.send_message(admin, text+"\n"+desc)

            user_state.pop(uid)
            return await msg.answer("⏳ Отправлено\nОжидай")

        # PARTNERSHIP
        if user_state[uid] == "part":
            text = f"""🤝 PARTNERSHIP
@{msg.from_user.username}"""

            desc = f"📌 {msg.text}"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅", callback_data=f"ok_{uid}")],
                [InlineKeyboardButton(text="❌", callback_data=f"no_{uid}")]
            ])

            for admin in ADMINS:
                await bot.send_message(admin, text+"\n"+desc, reply_markup=kb)

            user_state.pop(uid)
            return await msg.answer("⏳ Отправлено\nЖди ответа")

# ---------- ANNOUNCE ----------
@dp.message(Command("announce"))
async def announce(msg: Message):
    if not await verified(msg.from_user.id):
        return await msg.answer("❗ Нужен /verify")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 FA", callback_data="fa")],
        [InlineKeyboardButton(text="🏆 Лига", callback_data="lg")],
        [InlineKeyboardButton(text="🏟 Клуб", callback_data="cl")]
    ])
    await msg.answer("📢 Выбери тип\nЧерез кнопки ниже", reply_markup=kb)

@dp.callback_query(F.data == "fa")
async def fa(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="GK", callback_data="p_GK"),
         InlineKeyboardButton(text="CB", callback_data="p_CB")],
        [InlineKeyboardButton(text="CM", callback_data="p_CM"),
         InlineKeyboardButton(text="ST", callback_data="p_ST")]
    ])
    await call.message.answer("⚽ Выбери позицию\nКнопками", reply_markup=kb)

@dp.callback_query(F.data.startswith("p_"))
async def pos(call: CallbackQuery):
    uid = call.from_user.id
    user_state[uid] = "fa_text"
    user_state[uid+"_pos"] = call.data.split("_")[1]
    await call.message.answer("📝 Напиши о себе\nБез шаблона")

# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(msg: Message):
    user_state[msg.from_user.id] = "report"
    await msg.answer("🚨 Опиши проблему\nКратко и ясно")

# ---------- TRANSFER ----------
@dp.message(Command("transfer"))
async def transfer(msg: Message):
    user_state[msg.from_user.id] = "transfer"
    await msg.answer("📢 Напиши переход\nКлуб ➡️ клуб")

# ---------- PARTNERSHIP ----------
@dp.message(Command("partnership"))
async def part(msg: Message):
    await msg.answer("""🤝 PARTNERSHIP
1. | |
2. | |
3. | |""")

@dp.message(Command("setpartnership"))
async def setpart(msg: Message):
    user_state[msg.from_user.id] = "part"
    await msg.answer("🤝 Отправь заявку\nСсылка + инфо")

# ---------- ADMIN ----------
@dp.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "✅ Принято\nЖди пост")
    await call.message.edit_text("✅ Принято")

@dp.callback_query(F.data.startswith("no_"))
async def no(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "❌ Отклонено\nНе спамь")
    await call.message.edit_text("❌ Отклонено")

@dp.callback_query(F.data.startswith("ban_"))
async def ban(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    banned.add(uid)
    await bot.send_message(uid, "🚫 Бан\nАпелляция: @sqvnix")
    await call.message.edit_text("🚫 Забанен")

@dp.message(Command("unban"))
async def unban(msg: Message):
    if msg.from_user.id not in ADMINS:
        return
    try:
        uid = int(msg.text.split()[1])
        banned.discard(uid)
        await msg.answer("✅ Разбан\nГотово")
    except:
        await msg.answer("❗ Формат\n/unban id")

# ---------- RUN ----------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())