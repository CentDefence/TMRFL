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
        return await msg.answer("❗ Нужен /verify для использования команд ! ")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Free Agent", callback_data="fa")],
        [InlineKeyboardButton(text="🏆 Лига", callback_data="league")],
        [InlineKeyboardButton(text="🏟 Клуб", callback_data="club")]
    ])
    await msg.answer("📢 Выбери тип\nКнопками ниже. 
Free Agent - выставит тебя в роли Free Agent ! 
Лига - Даст прорекламировать свою же лигу ! 
Клуб - Поможет найти игроков в клуб ! ", reply_markup=kb)

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

@dp.message(Form.fa_text)
async def fa_send(msg: Message, state: FSMContext):
    if is_ban(msg.from_user.id):
        return await msg.answer("🚫 Бан\nАпелляция: @sqvnix")

    if not spam(msg.from_user.id):
        return await msg.answer("⏳ Подожди немного")

    data = await state.get_data()
    pos = data["pos"]

    # получаем Roblox ник
    async with aiosqlite.connect("db.sqlite") as db:
        cur = await db.execute("SELECT nick FROM users WHERE id=?", (msg.from_user.id,))
        row = await cur.fetchone()
        roblox = row[0] if row else "unknown"

    username = f"@{msg.from_user.username}" if msg.from_user.username else "нет юзера"

    text = f"""<b>📢 FREE AGENT ANNOUNCE</b>

👤 <b>{username}</b> | 🎮 <b>{roblox}</b>

⚽ <b>Position:</b> {pos}
📝 <b>About:</b> {msg.text}

#FreeAgent #TMRFL"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написать игроку", url=f"https://t.me/{msg.from_user.username}") if msg.from_user.username else InlineKeyboardButton(text="❌ Нет юзера", callback_data="none")],
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"ok_{msg.from_user.id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"no_{msg.from_user.id}")],
        [InlineKeyboardButton(text="🚫 Бан", callback_data=f"ban_{msg.from_user.id}")]
    ])

    for admin in ADMINS:
        await bot.send_message(admin, text, reply_markup=kb, parse_mode="HTML")

    await state.clear()
    await msg.answer("⏳ Заявка отправлена\nЖди ответа")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅", callback_data=f"ok_{msg.from_user.id}")],
        [InlineKeyboardButton(text="❌", callback_data=f"no_{msg.from_user.id}")],
        [InlineKeyboardButton(text="🚫 Ban", callback_data=f"ban_{msg.from_user.id}")]
    ])

    for admin in ADMINS:
        await bot.send_message(admin, text, reply_markup=kb)

    await state.clear()
    await msg.answer("⏳ Отправлено\nЖди ответа")

# ---------- LEAGUE ----------
@dp.callback_query(F.data == "league")
async def league(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.league)
    await call.message.answer(
        "🏆 Здраствуйте ! Пожалуйста отправьте ссылку на вашу лигу и также описание к ней ! 
Пример: t.me/RFLtransferMarket Очень крутой новостник ! "
    )

# ---------- CLUB -----------
@dp.callback_query(F.data == "club")
async def club(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.club)
    await call.message.answer(
        "🏟 Здраствуйте ! Пожалуйста отправьте ссылку на ваш новостник клуба и также описание к нему ! 
Пример: t.me/RFLtransferMarket Очень крутой новостник И мы требуем набор игроков ! "
    )

# ---------- REPORT ----------
@dp.message(Command("report"))
async def report(msg: Message, state: FSMContext):
    await state.set_state(Form.report)
    await msg.answer("🚨 Опишите жалобу\nПример жалобы: THAHKYOU200/@Sqvnix Слишком противен и нуждается в бане ! ")

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
    await msg.answer("⏳ Отправлено\nОжидайте ответа от администраторов бота. ")

# ---------- TRANSFER ----------
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    await state.set_state(Form.transfer)
    await msg.answer("📢 Напишите пожалуйста по шаблону /n@Sqvnix Клуб с которого вы перешли --> Клуб в который вы перешли.
пожалуйста пишите по шаблону.")

@dp.message(Form.transfer)
async def transfer_send(msg: Message, state: FSMContext):
    text = f"""📢 TRANSFER
@{msg.from_user.username}

➡️ {msg.text}"""

    for admin in ADMINS:
        await bot.send_message(admin, text)

    await state.clear()
    await msg.answer("⏳ Отправлено\nОжидай пожалуйста некоторое время ! ")

# ---------- ADMIN ----------
@dp.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "✅ Принято\nЖдите публикацию в наш канал ! ")
    await call.message.edit_text("✅ Принято")

@dp.callback_query(F.data.startswith("no_"))
async def no(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await bot.send_message(uid, "❌ Отклонено\n пожалуйста отредактируйте вашу заявку либо поработайте над ней.")
    await call.message.edit_text("❌ Отклонено")

@dp.callback_query(F.data.startswith("ban_"))
async def ban(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    banned.add(uid)
    await bot.send_message(uid, "🚫 Бан\nЧтобы подать аппеляцию напишите пожалуйста : @sqvnix")
    await call.message.edit_text("🚫 Вы ")

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