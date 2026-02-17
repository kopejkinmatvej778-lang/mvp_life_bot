
import logging
import asyncio
import os
import json
from datetime import date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database as db
import marathon_config as marathon
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN", "8406039171:AAHpxuxKi5vReNXpYrt5Iws3rDokoJ_gy78")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://mvp-app.amvera.io") 
ADMIN_ID = 726618588  # Hardcoded Admin ID

# Initialize
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher(storage=storage)

# --- STATES ---
class UserStates(StatesGroup):
    waiting_for_promo = State()

class AdminStates(StatesGroup):
    waiting_for_promo_code = State()
    waiting_for_promo_value = State()
    waiting_for_promo_usages = State()

# --- KEYBOARDS ---
def get_main_keyboard(user_id: int):
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0
    is_admin = (user_id == ADMIN_ID)
    has_access = (balance > 0) or is_admin
    
    kb = []
    
    # App Button (Only if Access Granted)
    if has_access:
        btn_app = KeyboardButton(text="🚀 ЗАПУСТИТЬ MVP OS", web_app=WebAppInfo(url=WEBAPP_URL or "https://google.com"))
        kb.append([btn_app])
        
    # Common Buttons
    btn_balance = KeyboardButton(text="💳 Баланс")
    btn_promo = KeyboardButton(text="🔑 Ввести промокод")
    kb.append([btn_balance, btn_promo])
    
    # Admin Buttons
    if is_admin:
        btn_create_promo = KeyboardButton(text="✏️ Создать промокод")
        btn_stats = KeyboardButton(text="📊 Статистика")
        btn_analysis = KeyboardButton(text="📈 Полный анализ")
        
        kb.append([btn_create_promo, btn_stats])
        kb.append([btn_analysis])
        
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)

# --- HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        db.create_user(user_id, message.from_user.username)
        await message.answer(f"👋 Привет, {message.from_user.first_name}! Dobro pozhalovat v MVP OS.")
    else:
        await message.answer(f"👋 С возвращением, {message.from_user.first_name}!")
        
    kb = get_main_keyboard(user_id)
    await message.answer("Главное меню:", reply_markup=kb)

# --- USER FEATURES ---

@dp.message(F.text == "💳 Баланс")
async def btn_balance(message: types.Message):
    user = db.get_user(message.from_user.id)
    if user:
        bal = user.get('balance', 0)
        await message.answer(f"💰 Твой баланс: **{bal} MVP**", parse_mode="Markdown")
    else:
        await message.answer("❌ Ошибка профиля. Нажми /start")

@dp.message(F.text == "🔑 Ввести промокод")
async def btn_promo(message: types.Message, state: FSMContext):
    await state.set_state(UserStates.waiting_for_promo)
    await message.answer("Введите промокод:", reply_markup=get_cancel_keyboard())

@dp.message(UserStates.waiting_for_promo)
async def process_promo(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    code = message.text.strip().upper()
    value = db.check_promocode(code)
    
    if value > 0:
        db.use_promocode(code)
        db.update_balance(message.from_user.id, value)
        await state.clear()
        
        # Show SUCCESS + ACCESS (since balance increased)
        kb = get_main_keyboard(message.from_user.id)
        
        await message.answer(f"✅ Промокод активирован!\n+ {value} MVP на баланс.\n🚀 Доступ к приложению открыт!", reply_markup=kb)
    else:
        await message.answer("❌ Неверный код или он закончился. Попробуй еще раз или нажми Отмена.")

# --- ADMIN FEATURES ---

@dp.message(F.text == "✏️ Создать промокод")
async def admin_create_promo(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await state.set_state(AdminStates.waiting_for_promo_code)
    await message.answer("Введите КОД (название):", reply_markup=get_cancel_keyboard())

@dp.message(AdminStates.waiting_for_promo_code)
async def admin_process_promo_code(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(message.from_user.id))
        return
        
    await state.update_data(code=message.text.upper())
    await state.set_state(AdminStates.waiting_for_promo_value)
    await message.answer("Введите СУММУ (число):")

@dp.message(AdminStates.waiting_for_promo_value)
async def admin_process_promo_value(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(message.from_user.id))
        return
        
    if not message.text.isdigit():
        await message.answer("❌ Введите число!")
        return
        
    await state.update_data(value=int(message.text))
    await state.set_state(AdminStates.waiting_for_promo_usages)
    await message.answer("Введите количество активаций (число):")

@dp.message(AdminStates.waiting_for_promo_usages)
async def admin_process_promo_usages(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    if not message.text.isdigit():
        await message.answer("❌ Введите число!")
        return

    data = await state.get_data()
    code = data['code']
    value = data['value']
    activations = int(message.text)
    
    success = db.create_promocode(code, value, activations)
    
    await state.clear()
    kb = get_main_keyboard(message.from_user.id)
    
    if success:
        await message.answer(f"✅ Промокод `{code}` создан!\nСумма: {value}\nАктиваций: {activations}", parse_mode="Markdown", reply_markup=kb)
    else:
        await message.answer("❌ Ошибка: Такой код уже существует.", reply_markup=kb)

@dp.message(F.text.in_({"📊 Статистика", "📈 Полный анализ"}))
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    stats = db.get_stats()
    
    msg = (
        f"📊 **Аналитика MVP OS**\n\n"
        f"👥 Всего пользователей: **{stats['total']}**\n"
        f"💰 Активных (Баланс > 0): **{stats['active']}**\n"
        f"♟ Сгенерировали стратегию: **{stats['strategy_users']}**\n"
    )
    await message.answer(msg, parse_mode="Markdown")


# --- SCHEDULER (Daily Tasks) ---

async def send_daily_tasks():
    if not bot: return
    
    today = date.today()
    delta = (today - marathon.START_DATE).days + 1
    
    # Check if marathon is active
    if delta < 1 or delta > 30:
        return

    # Find the current day's tasks
    day_data = next((d for d in marathon.MARATHON_DATA if d['day'] == delta), None)
    
    if not day_data:
        return

    # Try different ways to get users
    try:
        if hasattr(db, 'get_all_users_with_strategy'):
            users = db.get_all_users_with_strategy()
        else:
            # Fallback: get basic users list
            # We assume users object is structured or accessible
            users = db.get_all_users() 
            if isinstance(users, dict): # if it returns dict of users
                users = [{'user_id': uid} for uid in users.keys()]
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return

    clean_tasks = []
    for t in day_data['tasks']:
        # Format in config: "🧠 [CAT] Name: Desc (Зачем: ...)" or just "Task"
        clean_task = t
        if "(Зачем:" in t:
            clean_task = t.split("(Зачем:")[0].strip()
        elif "(Why:" in t:
             clean_task = t.split("(Why:")[0].strip()
            
        clean_tasks.append(f"• {clean_task}")

    tasks_str = "\n".join(clean_tasks)
    
    msg = (
        f"👋 Привет! Сегодня **День {delta}**.\n\n"
        f"🏆 **Тема:** {day_data['title']}\n\n"
        f"Вот твои задачи:\n"
        f"{tasks_str}\n\n"
        f"🚀 Заходи в приложение и отмечай выполнение!"
    )

    for u in users:
        try:
            user_id = u['user_id'] if isinstance(u, dict) else u
            await bot.send_message(
                user_id,
                msg,
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.05) 
        except Exception as e:
            logging.error(f"Failed to send to user: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_tasks, 'cron', hour=8, minute=0)
    scheduler.start()

# --- MAIN ---

async def start_bot():
    if not BOT_TOKEN:
        logging.warning("⚠️ BOT_TOKEN missing. Bot will not run.")
        return
    
    # db.init_db() is called in main.py, so skipping here or calling again is fine
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    
    start_scheduler()
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Polling error: {e}")
