import os, asyncio, base64, logging, json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# AI & DB
from openai import AsyncOpenAI
from sqlalchemy import select
from database.db_helper import init_db, async_session
from database.models import User, FoodLog

# Bot
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import user_handlers

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MVP_CORE")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SYSTEM STARTUP v4.0")
    await init_db()
    # Start Bot Polling in background
    token = os.getenv("BOT_TOKEN")
    if token:
        asyncio.create_task(run_bot(token))
    yield

app = FastAPI(lifespan=lifespan)

# --- CORS (Allow GitHub Pages) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for now to avoid headaches
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI LOGIC (Embedded) ---
async def analyze_food(text: str, image_b64: str = None):
    try:
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        
        msgs = [{"role": "system", "content": "You are a nutritional AI. Output JSON: {food_name, calories, protein, fat, carbs}."}]
        
        user_content = []
        if text: user_content.append({"type": "text", "text": text})
        
        if image_b64:
            # Fix header if missing
            if not image_b64.startswith("data:"):
                image_b64 = f"data:image/jpeg;base64,{image_b64}"
            user_content.append({"type": "image_url", "image_url": {"url": image_b64, "detail": "low"}})
            
        msgs.append({"role": "user", "content": user_content})
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        return None

# --- API ENDPOINTS ---

@app.get("/api/health")
async def health(): return {"status": "online", "version": "4.0"}

# 1. GET PROFILE & STATS
@app.get("/api/user/{uid}/profile")
async def get_profile(uid: str):
    try:
        user_id = int(str(uid).replace("/", ""))
    except: return JSONResponse({"error": "bad_id"}, 400)

    async with async_session() as session:
        # Get User
        res = await session.execute(select(User).filter(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(id=user_id)
            session.add(user)
            await session.commit()
            
        # Get Today's Logs
        today = datetime.utcnow().date()
        logs_res = await session.execute(select(FoodLog).filter(FoodLog.user_id == user_id))
        all_logs = logs_res.scalars().all()
        today_logs = [l for l in all_logs if l.created_at.date() == today]
        
        # Calculate Stats
        total_cal = sum(l.calories for l in today_logs)
        limit = user.daily_calorie_limit or 2500
        
        return {
            "status": "ok",
            "profile": {
                "height": user.height, "weight": user.weight, "goal": user.goal,
                "balance": user.balance
            },
            "nutrition": {
                "consumed": total_cal,
                "limit": limit,
                "protein": sum(l.protein or 0 for l in today_logs),
                "fat": sum(l.fat or 0 for l in today_logs),
                "carbs": sum(l.carbs or 0 for l in today_logs),
                # Goals (Dynamic)
                "p_goal": int(limit * 0.3 / 4),
                "f_goal": int(limit * 0.3 / 9),
                "c_goal": int(limit * 0.4 / 4)
            },
            "history": [
                {"name": l.food_name, "cal": l.calories, "time": l.created_at.isoformat()} 
                for l in sorted(today_logs, key=lambda x: x.created_at, reverse=True)
            ]
        }

# 2. ADD FOOD (Text or Photo)
class FoodReq(BaseModel):
    text: Optional[str] = None
    image_base64: Optional[str] = None

@app.post("/api/user/{uid}/add_food")
async def add_food(uid: str, data: FoodReq):
    user_id = int(str(uid).replace("/", ""))
    
    # Analyze
    ai_result = await analyze_food(data.text or "Food", data.image_base64)
    
    if ai_result:
        async with async_session() as session:
            # Ensure user exists
            await session.merge(User(id=user_id)) 
            
            # Save Log
            log = FoodLog(
                user_id=user_id,
                food_name=ai_result.get("food_name", "Unknown"),
                calories=ai_result.get("calories", 0),
                protein=ai_result.get("protein", 0),
                fat=ai_result.get("fat", 0),
                carbs=ai_result.get("carbs", 0)
            )
            session.add(log)
            await session.commit()
            
    return await get_profile(uid)

# 3. UPDATE PROFILE
@app.post("/api/user/{uid}/update_profile")
async def update_profile(uid: str, req: Request):
    data = await req.json()
    user_id = int(str(uid).replace("/", ""))
    
    async with async_session() as session:
        res = await session.execute(select(User).filter(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(id=user_id)
            session.add(user)
        
        if 'weight' in data: user.weight = data['weight']
        if 'height' in data: user.height = data['height']
        if 'goal' in data: user.goal = data['goal']
        if 'age' in data: user.age = data['age']
        if 'gender' in data: user.gender = data['gender']
        
        # Simple Logic for Calorie Limit
        bmr = 2000 # Default
        if user.weight and user.height and user.age:
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age
            if user.gender == 'male': bmr += 5
            else: bmr -= 161
        
        tdee = bmr * 1.55
        if user.goal == 'lose': tdee -= 500
        elif user.goal == 'gain': tdee += 300
        
        user.daily_calorie_limit = int(tdee)
        await session.commit()
        
    return await get_profile(uid)


# --- STATICS (MUST BE LAST) ---
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="web_app", html=True), name="static")

# --- BOT RUNNER ---
async def run_bot(token):
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user_handlers.router)
    # Remove webhook just in case
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 BOT POLLING STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
