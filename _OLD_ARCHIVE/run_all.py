import multiprocessing
import uvicorn
import asyncio
from bot import main as start_bot
from api import app as api_app

def run_api():
    print("🚀 Запуск API (FastAPI) на порту 8000...")
    uvicorn.run(api_app, host="0.0.0.0", port=8000)

def run_bot():
    print("🤖 Запуск Telegram Бота...")
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Используем мультипроцессорность для одновременного запуска
    api_process = multiprocessing.Process(target=run_api)
    bot_process = multiprocessing.Process(target=run_bot)

    api_process.start()
    bot_process.start()

    api_process.join()
    bot_process.join()
