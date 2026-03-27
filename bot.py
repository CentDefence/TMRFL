import asyncio
import os
import time
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("import asyncio
import os
import time
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("BOT_TOKEN")  # <-- твой токен
ADMINS = [8214590613]  # <-- твои ID админов

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

# ---------------- STATES ----------------
class Form(StatesGroup):
    verify = State()
    fa_position = State()
    fa_text = State()
    announce_league = State()
    announce_club = State()
    report_type = State()
    report_text = State()
    partnership_type = State()
    partnership_info = State()
    transfer_info = State()
    set_partnership_type = State()
    set_partnership_info = State()

# ---------------- DATABASE ----------------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            roblox TEXT
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

# ---------------- BACK BUTTON ----------------
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

@dp.message(Command("start"))
async def start(msg: Message):
    await back_start(CallbackQuery(message=msg, from_user=msg.from_user, data=""), FSMContext(dp))

# ---------------- VERIFY ----------------
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    await msg.answer("🛡 Введите ваш Roblox ник для использования команд. ⚠️ Ник можно менять только через ЛС владельца.")
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Верификация пройдена! Теперь доступны все команды.", reply_markup=BACK_KB)
    await state.clear()

# ---------------- ANNOUNCE ----------------
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

# ---------------- Free Agent ----------------
@dp.callback_query(F.data == "announce_fa")
async def announce_fa_cb(cb: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(row_width=4)
    for pos in ["GK", "CB", "CM", "LW", "RW", "ST", "ALL ROUNDER"]:
        kb.insert(InlineKeyboardButton(pos, callback_data=f"fa_pos_{pos}"))
    kb.add(InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start"))
    await cb.message.answer("📝 Выберите позицию (пример: GK, CB, CM, LW, RW, ST, ALL ROUNDER):", reply_markup=kb)

@dp.callback_query(F.data.startswith("fa_pos_"))
async def fa_position(cb: CallbackQuery, state: FSMContext):
    position = cb.data.split("_")[-1]
    await state.update_data(position=position)
    await cb.message.answer(f"✏️ Вы выбрали позицию: {position}\n\nНапишите немного о себе и своих навыках.\nПример:\nИграю за клуб X, опыт 3 года, сильные стороны: дриблинг, пас, позиционирование...", reply_markup=BACK_KB)
    await state.set_state(Form.fa_text)
    await cb.answer()

@dp.message(Form.fa_text)
async def fa_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    data = await state.get_data()
    position = data.get("position", "Не указано")
    text = f"""📢 *СВОБОДНЫЙ АГЕНТ*
💠 @{msg.from_user.username} - Ищет клуб
-- Позиция игрока: {position}
-- О себе: {msg.text}
#FreeAgent #TMRFL"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"fa_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"fa_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша заявка отправлена на рассмотрение!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- REPORT ----------------
@dp.message(Command("report"))
async def report(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⚠ Жалоба на игрока", callback_data="report_player")],
        [InlineKeyboardButton("⚠ Жалоба на клуб", callback_data="report_club")],
        [InlineKeyboardButton("⚠ Жалоба на лигу", callback_data="report_league")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип жалобы:", reply_markup=kb)

@dp.callback_query(F.data.startswith("report_"))
async def report_type(cb: CallbackQuery, state: FSMContext):
    r_type = cb.data.split("_")[1]
    await state.update_data(report_type=r_type)
    await cb.message.answer(f"✏️ Напишите подробности жалобы. Пример:\nНик игрока X нарушил правила, детали...", reply_markup=BACK_KB)
    await state.set_state(Form.report_text)
    await cb.answer()

@dp.message(Form.report_text)
async def report_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    data = await state.get_data()
    r_type = data.get("report_type")
    type_name = {"player":"Игрока","club":"Клуб","league":"Лигу"}.get(r_type, "Игрока")
    text = f"""🚨 *BlackList ALERT!*
💠 Ник игрока: @{msg.from_user.username}
Причина: {msg.text}
Тип: {type_name}
#TMRFL #Report"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"report_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"report_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша жалоба отправлена на рассмотрение!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- TRANSFER ----------------
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Переход в клуб", callback_data="transfer_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "transfer_club")
async def transfer_club(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("✏️ Пожалуйста, напишите с какого клуба вы перешли и в какой. Пример:\n'Клуб X ➡ Клуб Y'\nПосле заполнения информация отправится админам.", reply_markup=BACK_KB)
    await state.set_state(Form.transfer_info)

@dp.message(Form.transfer_info)
async def transfer_send(msg: Message, state: FSMContext):
    text = f"""❗️📢 ПЕРЕХОД ОФИЦИАЛЬНО
💠 @{msg.from_user.username} - {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"transfer_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"transfer_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb)
    await msg.answer("📨 Информация о переходе отправлена админам!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- PARTNERSHIP ----------------
@dp.message(Command("partnership"))
async def partnership(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🤝 Сотрудничество с лигами", callback_data="partner_league")],
        [InlineKeyboardButton("📰 Сотрудничество с новостниками", callback_data="partner_news")],
        [InlineKeyboardButton("🏟 Сотрудничество с клубами", callback_data="partner_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип партнерства:", reply_markup=kb)

@dp.callback_query(F.data.startswith("partner_"))
async def partnership_cb(cb: CallbackQuery, state: FSMContext):
    p_type = cb.data.split("_")[1]
    await state.update_data(partnership_type=p_type)
    await cb.message.answer(f"✏️ Пожалуйста, отправьте ссылку на {p_type} и расскажите о себе. Пример:\nСсылка: t.me/Example\nОписание: сотрудничество по турнирам...", reply_markup=BACK_KB)
    await state.set_state(Form.partnership_info)

@dp.message(Form.partnership_info)
async def partnership_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    p_type = data.get("partnership_type")
    text = f"""🤝 *Сотрудничество TMRFL с {p_type}*
💠 @{msg.from_user.username}
-- Информация: {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"partner_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"partner_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша заявка на партнерство отправлена на рассмотрение!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- ADMIN ACTIONS ----------------
@dp.callback_query(F.data.startswith("fa_ok_"))
async def fa_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша заявка Free Agent успешно принята! О вас скоро напишут в канале.", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("fa_no_"))
async def fa_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша заявка Free Agent отклонена. Не спамьте повторно заявки. Вопросы: t.me/TMRFLSUPPORT_bot", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("report_ok_"))
async def report_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша жалоба принята и находится на рассмотрении!", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("report_no_"))
async def report_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша жалоба отклонена. Пожалуйста, соблюдайте правила.", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("transfer_ok_"))
async def transfer_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Переход принят админом!", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("transfer_no_"))
async def transfer_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Переход отклонен админом.", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("partner_ok_"))
async def partner_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша заявка на партнерство принята!", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("partner_no_"))
async def partner_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша заявка на партнерство отклонена.", reply_markup=BACK_KB)
    await cb.answer()

# ---------------- RUN ----------------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())")  # <-- твой токен
ADMINS = [8214590613]  # <-- твои ID админов

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

# ---------------- STATES ----------------
class Form(StatesGroup):
    verify = State()
    fa_position = State()
    fa_text = State()
    announce_league = State()
    announce_club = State()
    report_type = State()
    report_text = State()
    partnership_type = State()
    partnership_info = State()
    transfer_info = State()
    set_partnership_type = State()
    set_partnership_info = State()

# ---------------- DATABASE ----------------
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            roblox TEXT
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

# ---------------- BACK BUTTON ----------------
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

@dp.message(Command("start"))
async def start(msg: Message):
    await back_start(CallbackQuery(message=msg, from_user=msg.from_user, data=""), FSMContext(dp))

# ---------------- VERIFY ----------------
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    await msg.answer("🛡 Введите ваш Roblox ник для использования команд. ⚠️ Ник можно менять только через ЛС владельца.")
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Верификация пройдена! Теперь доступны все команды.", reply_markup=BACK_KB)
    await state.clear()

# ---------------- ANNOUNCE ----------------
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

# ---------------- Free Agent ----------------
@dp.callback_query(F.data == "announce_fa")
async def announce_fa_cb(cb: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(row_width=4)
    for pos in ["GK", "CB", "CM", "LW", "RW", "ST", "ALL ROUNDER"]:
        kb.insert(InlineKeyboardButton(pos, callback_data=f"fa_pos_{pos}"))
    kb.add(InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start"))
    await cb.message.answer("📝 Выберите позицию (пример: GK, CB, CM, LW, RW, ST, ALL ROUNDER):", reply_markup=kb)

@dp.callback_query(F.data.startswith("fa_pos_"))
async def fa_position(cb: CallbackQuery, state: FSMContext):
    position = cb.data.split("_")[-1]
    await state.update_data(position=position)
    await cb.message.answer(f"✏️ Вы выбрали позицию: {position}\n\nНапишите немного о себе и своих навыках.\nПример:\nИграю за клуб X, опыт 3 года, сильные стороны: дриблинг, пас, позиционирование...", reply_markup=BACK_KB)
    await state.set_state(Form.fa_text)
    await cb.answer()

@dp.message(Form.fa_text)
async def fa_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    data = await state.get_data()
    position = data.get("position", "Не указано")
    text = f"""📢 *СВОБОДНЫЙ АГЕНТ*
💠 @{msg.from_user.username} - Ищет клуб
-- Позиция игрока: {position}
-- О себе: {msg.text}
#FreeAgent #TMRFL"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"fa_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"fa_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша заявка отправлена на рассмотрение!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- REPORT ----------------
@dp.message(Command("report"))
async def report(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⚠ Жалоба на игрока", callback_data="report_player")],
        [InlineKeyboardButton("⚠ Жалоба на клуб", callback_data="report_club")],
        [InlineKeyboardButton("⚠ Жалоба на лигу", callback_data="report_league")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип жалобы:", reply_markup=kb)

@dp.callback_query(F.data.startswith("report_"))
async def report_type(cb: CallbackQuery, state: FSMContext):
    r_type = cb.data.split("_")[1]
    await state.update_data(report_type=r_type)
    await cb.message.answer(f"✏️ Напишите подробности жалобы. Пример:\nНик игрока X нарушил правила, детали...", reply_markup=BACK_KB)
    await state.set_state(Form.report_text)
    await cb.answer()

@dp.message(Form.report_text)
async def report_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного")
    data = await state.get_data()
    r_type = data.get("report_type")
    type_name = {"player":"Игрока","club":"Клуб","league":"Лигу"}.get(r_type, "Игрока")
    text = f"""🚨 *BlackList ALERT!*
💠 Ник игрока: @{msg.from_user.username}
Причина: {msg.text}
Тип: {type_name}
#TMRFL #Report"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"report_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"report_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша жалоба отправлена на рассмотрение!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- TRANSFER ----------------
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Переход в клуб", callback_data="transfer_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "transfer_club")
async def transfer_club(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("✏️ Пожалуйста, напишите с какого клуба вы перешли и в какой. Пример:\n'Клуб X ➡ Клуб Y'\nПосле заполнения информация отправится админам.", reply_markup=BACK_KB)
    await state.set_state(Form.transfer_info)

@dp.message(Form.transfer_info)
async def transfer_send(msg: Message, state: FSMContext):
    text = f"""❗️📢 ПЕРЕХОД ОФИЦИАЛЬНО
💠 @{msg.from_user.username} - {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"transfer_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"transfer_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb)
    await msg.answer("📨 Информация о переходе отправлена админам!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- PARTNERSHIP ----------------
@dp.message(Command("partnership"))
async def partnership(msg: Message, state: FSMContext):
    if not await is_verified(msg.from_user.id):
        return await msg.answer("❌ Сначала пройди /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🤝 Сотрудничество с лигами", callback_data="partner_league")],
        [InlineKeyboardButton("📰 Сотрудничество с новостниками", callback_data="partner_news")],
        [InlineKeyboardButton("🏟 Сотрудничество с клубами", callback_data="partner_club")],
        [InlineKeyboardButton("🔙 Вернуться на старт", callback_data="back_start")]
    ])
    await msg.answer("📢 Выберите тип партнерства:", reply_markup=kb)

@dp.callback_query(F.data.startswith("partner_"))
async def partnership_cb(cb: CallbackQuery, state: FSMContext):
    p_type = cb.data.split("_")[1]
    await state.update_data(partnership_type=p_type)
    await cb.message.answer(f"✏️ Пожалуйста, отправьте ссылку на {p_type} и расскажите о себе. Пример:\nСсылка: t.me/Example\nОписание: сотрудничество по турнирам...", reply_markup=BACK_KB)
    await state.set_state(Form.partnership_info)

@dp.message(Form.partnership_info)
async def partnership_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    p_type = data.get("partnership_type")
    text = f"""🤝 *Сотрудничество TMRFL с {p_type}*
💠 @{msg.from_user.username}
-- Информация: {msg.text}"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"partner_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"partner_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша заявка на партнерство отправлена на рассмотрение!", reply_markup=BACK_KB)
    await state.clear()

# ---------------- ADMIN ACTIONS ----------------
@dp.callback_query(F.data.startswith("fa_ok_"))
async def fa_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша заявка Free Agent успешно принята! О вас скоро напишут в канале.", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("fa_no_"))
async def fa_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша заявка Free Agent отклонена. Не спамьте повторно заявки. Вопросы: t.me/TMRFLSUPPORT_bot", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("report_ok_"))
async def report_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша жалоба принята и находится на рассмотрении!", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("report_no_"))
async def report_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша жалоба отклонена. Пожалуйста, соблюдайте правила.", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("transfer_ok_"))
async def transfer_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Переход принят админом!", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("transfer_no_"))
async def transfer_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Переход отклонен админом.", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("partner_ok_"))
async def partner_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша заявка на партнерство принята!", reply_markup=BACK_KB)
    await cb.answer()

@dp.callback_query(F.data.startswith("partner_no_"))
async def partner_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша заявка на партнерство отклонена.", reply_markup=BACK_KB)
    await cb.answer()

# ---------------- RUN ----------------
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())