import asyncio
import aiosqlite
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

TOKEN = "8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA"
ADMINS = [8214590613]

bot = Bot(TOKEN)
dp = Dispatcher()

cooldown = {}
banned = set()

# ---------- FSM ----------
class Form(StatesGroup):
    verify = State()
    fa_text = State()
    report = State()
    transfer = State()
    partnership = State()

# ---------- DB ----------
async def init_db():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, nick TEXT)")
        await db.commit()

async def verified(uid):
    async with aiosqlite.connect("db.sqlite") as db:
        cur = await db.execute("SELECT * FROM users WHERE id=?", (uid,))
        return await cur.fetchone()

# ---------- CHECK ----------
def spam(uid):
    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 15:
        return False
    cooldown[uid] = now
    return True

def is_ban(uid):
    return uid in banned

# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer(f"""👋Здраствуйте !  {msg.from_user.first_name}
🎮 Трансфер Маркет RFL

📌 t.me/RFLtransferMarket

📋 Команды:
/verify
/announce
/report
/transfer
/partnership
/setpartnership""")

# ---------- VERIFY ----------
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    if await verified(msg.from_user.id):
        return await msg.answer("✅ Уже есть\nДоступ открыт")

    await state.set_state(Form.verify)
    await msg.answer("📝 Введи Roblox ник\n1 сообщением для открытие доступа к командам")

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("INSERT INTO users VALUES (?,?)", (msg.from_user.id, msg.text))
        await db.commit()

    await state.clear()
    await msg.answer("✅ Готово\nМожешь использовать команды")

# ---------- ANNOUNCE ----------
@dp.message(Command("announce"))
async def announce(msg: Message):
    if not await verified(msg.from_user.id):
        return await msg.answer("❗ Нужен /verify")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free Agent", callback_data="fa")],
        [InlineKeyboardButton(text="🏆 Лига", callback_data="league")],
        [InlineKeyboardButton(text="🏟 Клуб", callback_data="club")]
    ])
    await msg.answer("📢 Выбери тип\nКнопками ниже. Free Agent - выставит тебя в роли Free Agent ! Лига - Даст прорекламировать свою же лигу ! Клуб - Поможет найти игроков в клуб ! ", reply_markup=kb)

# ---------- FREE AGENT ----------
@dp.callback_query(F.data == "fa")
async def fa(call: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="GK", callback_data="pos_GK"),
         InlineKeyboardButton(text="CB", callback_data="pos_CB")],
        [InlineKeyboardButton(text="CM", callback_data="pos_CM"),
         InlineKeyboardButton(text="ST", callback_data="pos_ST")]
    ])
    await call.message.answer("⚽ Выбери позицию\nКнопками", reply_markup=kb)

@dp.callback_query(F.data.startswith("pos_"))
async def pos(call: CallbackQuery, state: FSMContext):
    await state.update_data(pos=call.data.split("_")[1])
    await state.set_state(Form.fa_text)
    await call.message.answer("📝 Напиши о себе\nБез шаблона")

@dp.message(Form.fa_text)
async def fa_send(msg: Message, state: FSMContext):
    if is_ban(msg.from_user.id):
        return await msg.answer("🚫 Бан\nАпелляция: @Sqvnix")

    if not spam(msg.from_user.id):
        return await msg.answer("⏳ Подожди буквально минуточку")

    data = await state.get_data()
    pos = data["pos"]

    text = f"""📢 FREE AGENT
@{msg.from_user.username} | {pos}

📝 {msg.text}
#FA #TMRFL"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data=f"ok_{msg.from_user.id}")],
        [InlineKeyboardButton(text="❌", callback_data=f"no_{msg.from_user.id}")],
        [InlineKeyboardButton(text="🚫 Ban", callback_data=f"ban_{msg.from_user.id}")]
    ])

    for admin in ADMINS:
        await bot.send_message(admin, text, reply_markup=kb)

    await state.clear()
    await msg.answer("⏳ Отправлено\nЖди ответа")

# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(msg: Message, state: FSMContext):
    await state.set_state(Form.report)
    await msg.answer("🚨 Опиши жалобу\nКратко")

@dp.message(Form.report)
async def rep_send(msg: Message, state: FSMContext):
    text = f"""🚨 REPORT
@{msg.from_user.username}

📌 {msg.text}"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data=f"ok_{msg.from_user.id}")],
        [InlineKeyboardButton(text="❌", callback_data=f"no_{msg.from_user.id}")]
    ])

    for admin in ADMINS:
        await bot.send_message(admin, text, reply_markup=kb)

    await state.clear()
    await msg.answer("⏳ Отправлено\nОжидай")

# ---------- TRANSFER ----------
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    await state.set_state(Form.transfer)
    await msg.answer("📢 Напиши переход\nКлуб➡️Клуб")

@dp.message(Form.transfer)
async def transfer_send(msg: Message, state: FSMContext):
    text = f"""📢 TRANSFER
@{msg.from_user.username}

➡️ {msg.text}"""

    for admin in ADMINS:
        await bot.send_message(admin, text)

    await state.clear()
    await msg.answer("⏳ Отправлено\nОжидай")

# ---------- PARTNERSHIP ----------
@dp.message(Command("partnership"))
async def part(msg: Message):
    await msg.answer("""🤝 PARTNERSHIP
1. | |
2. | |
3. | |""")

@dp.message(Command("setpartnership"))
async def setpart(msg: Message, state: FSMContext):
    await state.set_state(Form.partnership)
    await msg.answer("🤝 Отправь заявку\nСсылка + описание")

@dp.message(Form.partnership)
async def part_send(msg: Message, state: FSMContext):
    text = f"""🤝 PARTNERSHIP
@{msg.from_user.username}

📌 {msg.text}"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data=f"ok_{msg.from_user.id}")],
        [InlineKeyboardButton(text="❌", callback_data=f"no_{msg.from_user.id}")]
    ])

    for admin in ADMINS:
        await bot.send_message(admin, text, reply_markup=kb)

    await state.clear()
    await msg.answer("⏳ Отправлено\nЖди ответа")

# ---------- ADMIN ----------
@dp.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "✅ Принято\nЖди публикации")
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