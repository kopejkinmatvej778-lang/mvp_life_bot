from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.main_menu import get_main_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🔮 **Welcome to MVP Life OS v4.0**\n\nSystem is online. Ready to evolve?",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 PROFILE")
async def profile_btn(message: Message):
    await message.answer("Use the Web App ⚡ to manage your profile.")

@router.message(F.text == "💰 WALLET")
async def wallet_btn(message: Message):
    await message.answer("Balance available in Web App ⚡")
