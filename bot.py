import asyncio
import os
import time
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = os.getenv("8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA")  # вставьте токен
ADMINS = [8214590613]  # ваши ID админов

bot = Bot(TOKEN)
dp = Dispatcher()

COOLDOWN = 10
cooldowns = {}

# --- FSM States ---
class Form(StatesGroup):
    verify = State()
    fa_position = State()
    fa_info = State()
    league = State()
    club = State()
    transfer = State()
    report = State()
    set_partnership = State()
    partnership_info = State()

# --- БД ---
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                roblox TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS partnerships (
                user_id INTEGER,
                type TEXT,
                link TEXT,
                info TEXT
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

async def add_partnership(user_id, type_, link, info):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT INTO partnerships VALUES (?, ?, ?, ?)", (user_id, type_, link, info))
        await db.commit()

async def get_partnerships(type_=None):
    async with aiosqlite.connect("bot.db") as db:
        if type_:
            async with db.execute("SELECT user_id, link, info FROM partnerships WHERE type=?", (type_,)) as c:
                return await c.fetchall()
        else:
            async with db.execute("SELECT user_id, type, link, info FROM partnerships") as c:
                return await c.fetchall()

# --- AntiSpam ---
def anti_spam(user_id):
    now = time.time()
    if user_id in cooldowns and now - cooldowns[user_id] < COOLDOWN:
        return False
    cooldowns[user_id] = now
    return True

# --- Кнопка "Назад на старт" ---
def back_to_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться на старт", callback_data="start")]
    ])

# --- START ---
@dp.message(Command("start"))
async def start(msg: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("/announce"), KeyboardButton("/report")],
            [KeyboardButton("/transfer"), KeyboardButton("/verify")],
            [KeyboardButton("/partnership"), KeyboardButton("/setpartnership")]
        ], resize_keyboard=True
    )
    await msg.answer(
        f"👋 Привет! Это **Transfer Market RFL**.\n\n"
        f"Здесь вы можете сделать объявление о Free Agent, набор в лигу/клуб, перейти клуб или сотрудничать.\n\n"
        f"Ссылка на нас: [t.me/RFLtransferMarket](https://t.me/RFLtransferMarket)\n\n"
        f"Список команд вы видите ниже 👇", reply_markup=kb, parse_mode="Markdown"
    )

@dp.callback_query(F.data == "start")
async def cb_start(cb: CallbackQuery):
    await start(cb.message)
    await cb.answer()

# --- VERIFY ---
@dp.message(Command("verify"))
async def verify(msg: Message, state: FSMContext):
    if await get_user(msg.from_user.id):
        return await msg.answer("✅ Вы уже прошли Verify ранее!")
    await msg.answer(
        "🛡 Для использования всех команд, пожалуйста, введите свой ник Roblox.\n"
        "❗ Внимание: смена ника возможна только через ЛС владельца."
    )
    await state.set_state(Form.verify)

@dp.message(Form.verify)
async def save_verify(msg: Message, state: FSMContext):
    await add_user(msg.from_user.id, msg.text)
    await msg.answer("✅ Вы успешно прошли Verify!", reply_markup=back_to_start())
    await state.clear()

# --- ANNOUNCE ---
@dp.message(Command("announce"))
async def announce(msg: Message):
    if not await get_user(msg.from_user.id):
        return await msg.answer("❌ Сначала пройдите /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Free Agent", callback_data="fa")],
        [InlineKeyboardButton(text="🏆 Набор в Лигу", callback_data="league")],
        [InlineKeyboardButton(text="🏟 Набор в Клуб", callback_data="club")],
        [InlineKeyboardButton(text="📝 Другое", callback_data="other")],
        [InlineKeyboardButton(text="🔙 Вернуться на старт", callback_data="start")]
    ])
    await msg.answer(
        "Здравствуйте!\nВы хотите сделать объявление в TransferMarketRFL.\n"
        "Пожалуйста, выберите тему:", reply_markup=kb
    )

# --- Free Agent ---
@dp.callback_query(F.data == "fa")
async def fa_position(cb: CallbackQuery, state: FSMContext):
    positions_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=p, callback_data=f"pos_{p}") for p in ["GK", "CB", "CM", "LW", "RW", "ST", "AllRounder"]],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="start")]
    ])
    await cb.message.answer("Выберите вашу позицию (пример: ST) 👇", reply_markup=positions_kb)
    await state.set_state(Form.fa_position)
    await cb.answer()

@dp.callback_query(F.data.startswith("pos_"))
async def fa_choose_position(cb: CallbackQuery, state: FSMContext):
    position = cb.data[4:]
    await state.update_data(position=position)
    await cb.message.answer(f"Вы выбрали позицию: **{position}**\n\n"
                            "Теперь напишите немного о себе. Пример:\n"
                            "`Я атакующий игрок, люблю дриблинг и точные передачи.`",
                            parse_mode="Markdown")
    await state.set_state(Form.fa_info)
    await cb.answer()

@dp.message(Form.fa_info)
async def fa_send(msg: Message, state: FSMContext):
    if not anti_spam(msg.from_user.id):
        return await msg.answer("⏳ Подождите немного перед следующей отправкой")
    data = await state.get_data()
    position = data.get("position", "Не указана")
    text = f"""
📢 **СВОБОДНЫЙ АГЕНТ**

💠 @{msg.from_user.username} - Ищет клуб
-- Позиция игрока: {position}
P.s: {msg.text}

#FreeAgent #TMRFL
"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"fa_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"fa_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша заявка отправлена на рассмотрение", reply_markup=back_to_start())
    await state.clear()

@dp.callback_query(F.data.startswith("fa_ok_"))
async def fa_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша заявка Free Agent принята! О вас скоро напишут в канале!", reply_markup=back_to_start())
    await cb.answer("Принято")

@dp.callback_query(F.data.startswith("fa_no_"))
async def fa_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Извиняемся! Вашу заявку отклонили.\n"
                                "Пожалуйста, не спамьте заявки. Если есть вопросы — напишите в тикет: t.me/TMRFLSUPPORT_bot",
                           reply_markup=back_to_start())
    await cb.answer("Отклонено")

# --- TRANSFER ---
@dp.message(Command("transfer"))
async def transfer(msg: Message, state: FSMContext):
    if not await get_user(msg.from_user.id):
        return await msg.answer("❌ Сначала пройдите /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔄 Переход в клуб", callback_data="transfer_club")],
        [InlineKeyboardButton("🔙 Назад", callback_data="start")]
    ])
    await msg.answer("Выберите действие:", reply_markup=kb)

@dp.callback_query(F.data == "transfer_club")
async def transfer_template(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer(
        f"💠 Пример заполнения:\n"
        f"@{cb.from_user.username} - клуб с которого вы перешли ➡ клуб в который вы перешли\n\n"
        f"Скопируйте этот шаблон и заполните, затем отправьте сюда"
    )
    await state.set_state(Form.transfer)
    await cb.answer()

@dp.message(Form.transfer)
async def transfer_send(msg: Message):
    template = f"@{msg.from_user.username} - "
    if "➡" not in msg.text or not msg.text.startswith(template):
        return await msg.answer("❌ Пожалуйста, используйте **только шаблон** и отправьте корректно!", parse_mode="Markdown")
    text = f"❗️📢 ПЕРЕХОД ОФИЦИАЛЬНО\n\n💠 {msg.text}\nЮзернейм: @{msg.from_user.username}"
    for a in ADMINS:
        await bot.send_message(a, text)
    await msg.answer("✅ Ваша информация отправлена админам!", reply_markup=back_to_start())

# --- SET PARTNERSHIP ---
@dp.message(Command("setpartnership"))
async def set_partnership(msg: Message, state: FSMContext):
    if not await get_user(msg.from_user.id):
        return await msg.answer("❌ Сначала пройдите /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🤝 Сотрудничество с Лигой", callback_data="partnership_league")],
        [InlineKeyboardButton("🤝 Сотрудничество с Клубом", callback_data="partnership_club")],
        [InlineKeyboardButton("🤝 Сотрудничество с Новостником", callback_data="partnership_news")],
        [InlineKeyboardButton("🔙 Назад", callback_data="start")]
    ])
    await msg.answer("Выберите тип сотрудничества:", reply_markup=kb)

@dp.callback_query(F.data.startswith("partnership_"))
async def partnership_info(cb: CallbackQuery, state: FSMContext):
    type_ = cb.data.split("_")[1]
    await state.update_data(type_=type_)
    await cb.message.answer(f"Вы выбрали сотрудничество с **{type_.capitalize()}**\n"
                            "Отправьте ссылку на ресурс и краткую информацию о себе (пример: канал/клуб/лига, описание).",
                            parse_mode="Markdown")
    await state.set_state(Form.partnership_info)
    await cb.answer()

@dp.message(Form.partnership_info)
async def partnership_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    type_ = data.get("type_")
    parts = msg.text.split("\n", 1)
    link = parts[0] if parts else ""
    info = parts[1] if len(parts) > 1 else ""
    await add_partnership(msg.from_user.id, type_, link, info)
    text = f"📢 **НОВАЯ ЗАЯВКА НА ПАРТНЕРСТВО**\n\nТип: {type_.capitalize()}\n💠 @{msg.from_user.username}\nСсылка: {link}\nОписание: {info}"
    for a in ADMINS:
        await bot.send_message(a, text, parse_mode="Markdown")
    await msg.answer("✅ Ваша заявка отправлена на рассмотрение!", reply_markup=back_to_start())
    await state.clear()

# --- PARTNERSHIP LIST ---
@dp.message(Command("partnership"))
async def partnership_list(msg: Message):
    if not await get_user(msg.from_user.id):
        return await msg.answer("❌ Сначала пройдите /verify")
    data = await get_partnerships()
    if not data:
        return await msg.answer("Список партнерств пока пуст.")
    text = "📜 **Список партнерств:**\n\n"
    for u_id, type_, link, info in data:
        text += f"💠 {type_.capitalize()} - {link}\nОписание: {info}\n\n"
    await msg.answer(text, parse_mode="Markdown", reply_markup=back_to_start())

# --- REPORT ---
@dp.message(Command("report"))
async def report(msg: Message, state: FSMContext):
    if not await get_user(msg.from_user.id):
        return await msg.answer("❌ Сначала пройдите /verify")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⚠ Жалоба на Лигу", callback_data="report_league")],
        [InlineKeyboardButton("⚠ Жалоба на Игрока", callback_data="report_player")],
        [InlineKeyboardButton("⚠ Жалоба на Клуб", callback_data="report_club")],
        [InlineKeyboardButton("🔙 Назад", callback_data="start")]
    ])
    await msg.answer("Выберите тип жалобы:", reply_markup=kb)

@dp.callback_query(F.data.startswith("report_"))
async def report_type(cb: CallbackQuery, state: FSMContext):
    type_ = cb.data.split("_")[1]
    await state.update_data(report_type=type_)
    await cb.message.answer(f"Отправьте информацию о жалобе (пример: Ник, Причина, Срок)")
    await state.set_state(Form.report)
    await cb.answer()

@dp.message(Form.report)
async def report_send(msg: Message, state: FSMContext):
    data = await state.get_data()
    type_ = data.get("report_type")
    text = f"🚨 **BlackList ALERT**\nТип: {type_}\n💠 Ник: @{msg.from_user.username}\nПричина/Срок: {msg.text}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"report_ok_{msg.from_user.id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"report_no_{msg.from_user.id}")]
    ])
    for a in ADMINS:
        await bot.send_message(a, text, reply_markup=kb, parse_mode="Markdown")
    await msg.answer("📨 Ваша жалоба отправлена на рассмотрение", reply_markup=back_to_start())
    await state.clear()

@dp.callback_query(F.data.startswith("report_ok_"))
async def report_ok(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "✅ Ваша жалоба принята!", reply_markup=back_to_start())
    await cb.answer("Принято")

@dp.callback_query(F.data.startswith("report_no_"))
async def report_no(cb: CallbackQuery):
    uid = int(cb.data.split("_")[2])
    await bot.send_message(uid, "❌ Ваша жалоба отклонена!", reply_markup=back_to_start())
    await cb.answer("Отклонено")

# --- RUN ---
async def main():
    await init_db()
    await dp.start_polling(bot)

asyncio.run(main())