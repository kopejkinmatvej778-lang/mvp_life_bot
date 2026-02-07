
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
import os
import logging
import json
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any

# Internal Modules
import database as db
import bot
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
PORT = int(os.getenv("PORT", 8000))
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "sk-uaCAiWtESPfzTUm2kUqkOiupCBFB1sDz") 

# Initialize App
app = FastAPI(title="MVP OS Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# OpenAI Client
client = OpenAI(
    api_key=PROXY_API_KEY or "dummy_key", 
    base_url="https://api.proxyapi.ru/openai/v1"
)

# --- LIFECYCLE ---
@app.on_event("startup")
async def on_startup():
    # Initialize DB
    db.init_db()
    # Start Bot (Polling) in background
    if os.getenv("BOT_TOKEN"):
        try:
            asyncio.create_task(bot.start_bot())
        except Exception as e:
            logging.error(f"CRITICAL: Failed to start Telegram Bot: {e}")

# --- MODELS ---
class FoodRequest(BaseModel):
    text: str

class StrategyRequest(BaseModel):
    focus: str
    answers: List[str]

class SyncRequest(BaseModel):
    user_id: int
    username: Optional[str] = "Anon"
    strategy_data: Dict[str, Any]

# --- API ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "MVP OS Backend", "bot_active": bool(os.getenv("BOT_TOKEN"))}

@app.post("/sync_strategy")
def sync_strategy(req: SyncRequest):
    logging.info(f"🔄 Syncing strategy for User {req.user_id}")
    user = db.get_user(req.user_id)
    if not user:
        db.create_user(req.user_id, req.username)
    db.save_strategy(req.user_id, req.strategy_data)
    return {"status": "synced"}

@app.post("/analyze_food")
def analyze_food_endpoint(req: FoodRequest):
    if not PROXY_API_KEY:
        raise HTTPException(status_code=500, detail="Server API Key not configured")
    
    prompt = f"""
    Ты — профессиональный нутрициолог.
    Твоя задача: найти все продукты в тексте и вернуть их примерную калорийность и БЖУ.
    Текст пользователя: "{req.text}"
    
    Верни ТОЛЬКО валидный JSON (без Markdown):
    {{
        "name": "Название блюда",
        "calories": 0, "protein": 0, "fat": 0, "carbs": 0
    }}
    Если это не еда, calories: 0.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = completion.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        logging.error(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_strategy")
def generate_strategy_endpoint(req: StrategyRequest):
    if not PROXY_API_KEY:
        raise HTTPException(status_code=500, detail="Server API Key not configured")

    system_prompt = "Ты — Titan AI, элитный стратег. Формат ответа: ТОЛЬКО JSON."
    user_prompt = f"""
    Цель: {req.focus}
    Ответы: {", ".join(req.answers)}
    
    Создай JSON:
    {{
        "status": "success",
        "data": {{
            "focus": "{req.focus}",
            "stats": {{ "complexity": 50, "time_required": 50, "sustainability": 50, "impact": 50 }},
            "days": [ {{ "day": 1, "title": "...", "tasks": ["..."] }} ]
        }}
    }}
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5
        )
        content = completion.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        logging.error(f"Strategy Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.staticfiles import StaticFiles

# ... existing imports ...

# --- STATIC FILES (Frontend) ---
# Serve static files (HTML, CSS, JS) from 'static' directory
# html=True allows serving index.html at root automatically
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
else:
    # Fallback if static folder missing (e.g. dev mode)
    @app.get("/")
    async def serve_index():
        return {"message": "Static files not found. Please ensure 'static' folder exists with index.html."}

# Optional: Serve other static assets if any
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
