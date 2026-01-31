"""
Миграция: Добавление системы трекинга еды
- Добавляет поле daily_calorie_limit в users
- Создает таблицу food_logs
"""

import asyncio
import sys
import os

# Добавляем корневую директорию проекта в sys.path, чтобы Python видел папку database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from database.db_helper import async_session, engine
from database.models import Base

async def migrate():
    async with engine.begin() as conn:
        # 1. Добавляем колонку daily_calorie_limit в users
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN daily_calorie_limit INTEGER DEFAULT 2500"
            ))
            print("✅ Добавлено поле daily_calorie_limit")
        except Exception as e:
            print(f"⚠️ Поле daily_calorie_limit уже существует или ошибка: {e}")
        
        # 2. Создаем таблицу food_logs
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблица food_logs создана (если не существовала)")

if __name__ == "__main__":
    print("Запуск миграции...")
    asyncio.run(migrate())
    print("Миграция завершена!")
