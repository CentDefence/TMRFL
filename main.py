import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("BOT_TOKEN")
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
    partner_type