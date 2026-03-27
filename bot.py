import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite

TOKEN = "8712937703:AAEULzwqOk_XmNJhTwb2-OX4ISZ7pvBwbbA"
ADMINS = [8214590613]  # список админов

bot = Bot(token=TOKEN)
dp = Dispatcher()

# FSM для разных форм
class VerifyStates(StatesGroup):
    waiting_for_nick = State()

class AnnounceStates(StatesGroup):
    waiting_for_fa = State()
    waiting_for_league = State()
    waiting_for_club = State()
    waiting_for_other = State()

class ReportStates(StatesGroup):
    waiting_for_report_type = State()
    waiting_for_report_text = State()

class PartnershipStates(StatesGroup):
    waiting_for_type = State()
    waiting_for_info = State()

class TransferStates(StatesGroup):
    waiting_for_transfer_info = State()

# --- База данных для верификации ---
async def create_db():
    async with aiosqlite.connect("tmrfl.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS verified (
            user_id INTEGER PRIMARY KEY,
            roblox_nick TEXT
        )
        """)
        await db.commit()
asyncio.run(create_db())

# Проверка верификации
async def is_verified(user_id: int):
    async with aiosqlite.connect("tmrfl.db") as db:
        async with db.execute("SELECT * FROM verified WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

# --- START ---
@dp.message(Command("start"))
async def start(message: Message):
    text = (
        f"👋 Привет, {message.from_user.full_name}!\n"
        "🎮 Трансфер Маркет RFL\n\n"
        "Здесь можно создавать объявления Free Agent, набор в лигу/клуб, жалобы, партнерства и многое другое!\n\n"
        "📌 Ссылка: t.me/RFLtransferMarket\n\n"
        "📋 Список команд:\n"
        "/verify - пройти верификацию (обязательно)\n"
        "/announce - создать объявление\n"
        "/report - пожаловаться\n"
        "/transfer - переход игрока\n"
        "/partnership - сотрудничество\n"
        "/setpartnership - стать партнером"
    )
    await message.answer(text)

# --- VERIFY ---
@dp.message(Command("verify"))
async def verify(message: Message, state: FSMContext):
    if await is_verified(message.from_user.id):
        await message.answer("✅ Вы уже прошли верификацию. Чтобы сменить ник, напишите администратору.")
        return
    await message.answer("✏️ Пожалуйста, укажите ваш ник Roblox (смена ника только через ЛС админа!).")
    await state.set_state(VerifyStates.waiting_for_nick)

@dp.message(VerifyStates.waiting_for_nick)
async def process_verify(message: Message, state: FSMContext):
    nick = message.text
    async with aiosqlite.connect("tmrfl.db") as db:
        await db.execute("INSERT INTO verified (user_id, roblox_nick) VALUES (?, ?)",
                         (message.from_user.id, nick))
        await db.commit()
    await state.clear()
    await message.answer(f"✅ Верификация успешна! Ваш ник: {nick}")

# --- ANNOUNCE ---
@dp.message(Command("announce"))
async def announce(message: Message):
    if not await is_verified(message.from_user.id):
        await message.answer("❌ Сначала пройдите верификацию через /verify")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("📢 Free Agent", callback_data="fa")],
            [InlineKeyboardButton("🏆 Набор в Лигу", callback_data="league")],
            [InlineKeyboardButton("⚽ Набор в Клуб", callback_data="club")],
            [InlineKeyboardButton("📝 Другое", callback_data="other")],
            [InlineKeyboardButton("↩️ Вернуться на старт", callback_data="start")]
        ]
    )
    await message.answer("Выберите тип объявления:", reply_markup=kb)

# --- CALLBACKS ANNOUNCE ---
@dp.callback_query(F.data.in_(["fa", "league", "club", "other", "start"]))
async def announce_buttons(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username or call.from_user.full_name
    if call.data == "start":
        await call.message.delete()
        await start(call.message)
        return

    if not await is_verified(user_id):
        await call.message.answer("❌ Сначала пройдите верификацию через /verify")
        return

    if call.data == "fa":
        await call.message.answer("✏️ Укажите позиции и немного о себе.")
        await state.set_state(AnnounceStates.waiting_for_fa)
    elif call.data == "league":
        await call.message.answer("✏️ Укажите ссылку на лигу, количество мест и детали регистрации.")
        await state.set_state(AnnounceStates.waiting_for_league)
    elif call.data == "club":
        await call.message.answer("✏️ Укажите название клуба и расскажите о себе.")
        await state.set_state(AnnounceStates.waiting_for_club)
    elif call.data == "other":
        await call.message.answer("✏️ Опишите информацию для другого типа объявления.")
        await state.set_state(AnnounceStates.waiting_for_other)

# --- ANNOUNCE FSM HANDLERS ---
async def send_admin_announcement(user_id, username, text, kind):
    emoji_map = {"fa":"📢 СВОБОДНЫЙ АГЕНТ", "league":"📢 НАБОР В ЛИГУ", "club":"📢 НАБОР В КЛУБ", "other":"📢 ДРУГОЕ"}
    tags = {"fa":"#FreeAgent #TMRFL", "league":"#LeagueAnnounce #TMRFL", "club":"#LeagueAnnounce #TMRFL", "other":"#TMRFL"}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Принять", callback_data=f"accept_{kind}_{user_id}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{kind}_{user_id}")]
    ])
    for admin in ADMINS:
        await bot.send_message(admin,
            f"{emoji_map[kind]}\n\n💠 @{username}\n{text}\n{tags[kind]}",
            reply_markup=kb
        )

@dp.message(AnnounceStates.waiting_for_fa)
async def fa_handler(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    await send_admin_announcement(message.from_user.id, username, message.text, "fa")
    await state.clear()
    await message.answer("✅ Ваша заявка отправлена админам!")

@dp.message(AnnounceStates.waiting_for_league)
async def league_handler(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    await send_admin_announcement(message.from_user.id, username, message.text, "league")
    await state.clear()
    await message.answer("✅ Ваша заявка отправлена админам!")

@dp.message(AnnounceStates.waiting_for_club)
async def club_handler(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    await send_admin_announcement(message.from_user.id, username, message.text, "club")
    await state.clear()
    await message.answer("✅ Ваша заявка отправлена админам!")

@dp.message(AnnounceStates.waiting_for_other)
async def other_handler(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    await send_admin_announcement(message.from_user.id, username, message.text, "other")
    await state.clear()
    await message.answer("✅ Ваша заявка отправлена админам!")

# --- ADMIN ACCEPT/REJECT ---
@dp.callback_query(F.data.regexp(r'^(accept|reject)_(fa|league|club|other)_(\d+)$'))
async def admin_decision(call: CallbackQuery):
    action, kind, user_id = call.data.split("_")[0], call.data.split("_")[1], int(call.data.split("_")[2])
    if action == "accept":
        await bot.send_message(user_id, "✅ Ваша заявку приняли! О вас скоро напишут в канале!")
    else:
        await bot.send_message(user_id, "❌ Извиняемся! Вашу заявку не приняли. Вопросы: t.me/TMRFLSUPPORT_bot")
    await call.message.edit_reply_markup(None)

# --- Тут можно аналогично сделать /report, /transfer, /partnership и /setpartnership по такому же шаблону ---

# --- RUN ---
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))