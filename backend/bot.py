import logging
import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database as db
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN", "8406039171:AAHpxuxKi5vReNXpYrt5Iws3rDokoJ_gy78")
WEBAPP_URL = os.getenv("WEBAPP_URL") # https://...amvera.io/index.html
ADMIN_ID = int(os.getenv("ADMIN_ID", "5765707209"))

# Initialize
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

# --- KEYBOARDS ---
def get_start_keyboard(user_id: int, has_access: bool):
    kb = []
    
    if has_access:
        # Long "Open App" Button
        btn_app = KeyboardButton(text="🚀 ЗАПУСТИТЬ MVP OS", web_app=WebAppInfo(url=WEBAPP_URL or "https://google.com"))
        kb.append([btn_app])
    
    # Check Admin
    if user_id == ADMIN_ID:
        btn_admin = KeyboardButton(text="👮 Админка")
        kb.append([btn_admin])
        
    if not kb:
        return types.ReplyKeyboardRemove()
        
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    if not user:
        db.create_user(user_id, message.from_user.username)
        user = {'balance': 0}
    
    is_admin = (user_id == ADMIN_ID)
    has_access = (user['balance'] > 0) or is_admin
    
    kb = get_start_keyboard(user_id, has_access)
    
    if has_access:
        await message.answer(
            "👋 **Добро пожаловать в MVP!**\n\nСистема готова к работе.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🔒 **Доступ ограничен**\n\nДля активации системы введите **ПРОМОКОД**:",
            parse_mode="Markdown",
            reply_markup=kb # Might act as Reset if admin needs to remove keyboard but here admin gets button
        )

# text "👮 Админка" handler
@dp.message(F.text == "👮 Админка")
async def btn_admin_click(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await show_admin_panel(message)

# /admin command handler
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await show_admin_panel(message)

async def show_admin_panel(message: types.Message):
    users = db.get_all_users_with_strategy() # Approximate count
    
    msg = (
        f"📊 **Панель Администратора**\n\n"
        f"👥 Пользователей с планом: {len(users)}\n"
        f"💰 Чтобы создать промокод:\n"
        f"`/newpromo КОД АКТИВАЦИИ СУММА`\n"
        f"Пример: `/newpromo VIP2026 10 100`"
    )
    await message.answer(msg, parse_mode="Markdown")

@dp.message(Command("newpromo"))
async def cmd_newpromo(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    try:
        # Format: /newpromo CODE COUNT VALUE
        parts = message.text.split()
        if len(parts) != 4:
            await message.answer("❌ Формат: `/newpromo КОД КОЛ-ВО СУММА`", parse_mode="Markdown")
            return
            
        code = parts[1].strip().upper()
        activations = int(parts[2])
        value = int(parts[3])
        
        success = db.create_promocode(code, value, activations)
        if success:
            await message.answer(f"✅ Промокод `{code}` создан!\nАктиваций: {activations}\nСумма: {value}", parse_mode="Markdown")
        else:
            await message.answer("❌ Такой код уже существует!")
            
    except ValueError:
        await message.answer("❌ Кол-во и Сумма должны быть числами.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(F.text)
async def handle_text(message: types.Message):
    # Ignore admin button handled above
    if message.text == "👮 Админка": return

    user_id = message.from_user.id    
    user = db.get_user(user_id)
    if not user: return
    
    # If user has no access, try as promocode
    if user['balance'] == 0 and user_id != ADMIN_ID:
        code = message.text.strip().upper()
        value = db.check_promocode(code)
        
        if value > 0:
            db.use_promocode(code)
            db.update_balance(user_id, value)
            
            # Show Success + Access Button
            kb = get_start_keyboard(user_id, True)
            await message.answer(
                f"✅ **Промокод активирован!**\nБаланс пополнен на {value}.\nДоступ открыт.",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Неверный промокод (или закончился).")
            
    else:
        # Chat logic for active users
        # Maybe just ignore or echo
        pass


# --- SCHEDULER (Daily Tasks) ---
async def send_daily_tasks():
    if not bot: return
    users = db.get_all_users_with_strategy() # Actually need all users? No, only with strategy
    
    for u in users:
        try:
            # Logic: If strategy exists, send ping
            await bot.send_message(
                u['user_id'],
                "🌅 **MVP OS: Начало дня**\n\nТвой план действий готов. Зайди в приложение, чтобы закрыть задачи!"
            )
        except Exception as e:
            logging.error(f"Failed to send to {u['user_id']}: {e}")

# Start Scheduler
def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_tasks, 'cron', hour=7, minute=0)
    scheduler.start()

# --- MAIN ---
async def start_bot():
    if not BOT_TOKEN:
        logging.warning("⚠️ BOT_TOKEN missing. Bot will not run.")
        return
    
    db.init_db()
    start_scheduler()
    await dp.start_polling(bot)
