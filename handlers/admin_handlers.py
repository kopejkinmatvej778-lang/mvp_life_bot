from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.db_helper import async_session
from database.models import User, Task
from sqlalchemy import select
from utils.ai_helper import get_ai_response
import os

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID") or 5765707209)

@router.message(Command("admin"))
@router.message(F.text == "🛠 ADMIN PANEL")
@router.message(F.text == "SECRET_ADMIN_LOGIN")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав доступа к админ-панели.")
        return

    async with async_session() as session:
        # Статика пользователей
        users_res = await session.execute(select(User))
        users = users_res.scalars().all()
        
        # Статика задач
        tasks_res = await session.execute(select(Task))
        tasks = tasks_res.scalars().all()
        
        completed = len([t for t in tasks if t.is_completed])
        paid_users = len([u for u in users if (u.balance and u.balance > 0)])
        
        report = (
            "🛠 **ADMIN PANEL: MVP Life OS**\n\n"
            f"👥 Всего пользователей: **{len(users)}**\n"
            f"💎 Платных пользователей: **{paid_users}**\n"
            f"✅ Выполнено задач: **{completed}** / {len(tasks)}\n"
            f"📈 Ср. продуктивность: **{int(completed/len(tasks)*100) if tasks else 0}%**\n\n"
            "Выбери действие:\n"
            "/analyze_all — Сделать AI-анализ всей системы\n"
            "/list_users — Список активных героев"
        )
        await message.answer(report)

@router.message(Command("analyze_all"))
async def analyze_system(message: Message):
    if message.from_user.id != ADMIN_ID: return

    await message.answer("🧠 ИИ анализирует данные системы... Пожалуйста, подождите.")
    
    async with async_session() as session:
        tasks_res = await session.execute(select(Task))
        all_tasks = tasks_res.scalars().all()
        
        # Готовим краткий отчет для ИИ
        task_data = ""
        for t in all_tasks[:50]: # Берем последние 50 для контекста
            status = "✅" if t.is_completed else "❌"
            task_data += f"- {t.title} ({t.category}): {status}\n"

        prompt = (
            "Проанализируй эти данные о выполненных задачах пользователей за сегодня. "
            "Дай краткий отчет: какие категории проседают, а где пользователи молодцы. "
            "Дай одну рекомендацию, какую функцию добавить в бота завтра, чтобы поднять вовлеченность.\n\n"
            f"ДАННЫЕ:\n{task_data}"
        )
        
        ai_analysis = await get_ai_response(prompt)
        await message.answer(f"📊 **AI АНАЛИЗ СИСТЕМЫ:**\n\n{ai_analysis}")
