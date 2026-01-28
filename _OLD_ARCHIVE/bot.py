import os, logging, asyncio, base64, json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import uvicorn
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

# Project Imports
from database.db_helper import init_db, async_session
from database.models import User, FoodLog, Task
from handlers import user_handlers, admin_handlers
from utils.ai_helper import process_food_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MVP_STABLE")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 STARTING V14.0 (SLOT FIX)...")
    await init_db()
    yield

# Включаем strict_slashes=False, чтобы /api и /api/ работали одинаково
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def diagnostic_middleware(request: Request, call_next):
    # ЛОГ ПРЯМО В ПАНЕЛЬ AMVERA
    logger.info(f"📡 INCOMING: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"💾 OUTGOING: {response.status_code}")
    return response

class FoodReq(BaseModel): text: str

async def fetch_user_data(uid):
    uid_clean = str(uid).strip().replace("/", "") # Чистим от лишних слешей
    try:
        user_id = int(uid_clean)
    except:
        return {"error": "invalid_id", "uid_received": uid_clean}

    async with async_session() as session:
        res = await session.execute(
            select(User).filter(User.id == user_id).options(selectinload(User.food_logs))
        )
        u = res.scalar_one_or_none()
        if not u:
            u = User(id=user_id, daily_calorie_limit=2500)
            session.add(u)
            await session.commit()
            return {"stats": {"total_calories": 0, "limit": 2500}, "history": []}
        
        today = datetime.utcnow().date()
        logs = [l for l in u.food_logs if l.created_at.date() == today]
        return {
            "stats": {
                "total_calories": sum(l.calories for l in logs),
                "total_protein": sum(l.protein for l in logs),
                "total_fat": sum(l.fat for l in logs),
                "total_carbs": sum(l.carbs for l in logs),
                "limit": u.daily_calorie_limit or 2500,
                # Macros not stored in DB, strictly calculated or defaults
                "protein_goal": int((u.daily_calorie_limit or 2500) * 0.3 / 4),
                "fat_goal": int((u.daily_calorie_limit or 2500) * 0.3 / 9),
                "carbs_goal": int((u.daily_calorie_limit or 2500) * 0.4 / 4)
            },
            "history": [
                {
                    "food_name": l.food_name, 
                    "calories": l.calories,
                    "time": l.created_at.isoformat(),
                    "photo_file_id": l.photo_file_id if hasattr(l, 'photo_file_id') else None
                } for l in sorted(logs, key=lambda x: x.created_at, reverse=True)
            ]
        }

@app.get("/api/health")
async def health(): return {"status": "ok", "v": "14.0"}

# API Маршруты (Добавляем варианты со слешем и без)
@app.get("/api/v1/user/{uid}/stats")
@app.get("/api/v1/user/{uid}/stats/")
async def get_stats(uid: str):
    return JSONResponse(content=await fetch_user_data(uid))

@app.post("/api/v1/user/{uid}/food/text")
@app.post("/api/v1/user/{uid}/food/text/")
async def add_food_text(uid: str, data: FoodReq):
    ai = await process_food_chat(data.text)
    if ai and ai.get('food_data'):
        async with async_session() as session:
            try:
                user_id = int(str(uid).replace("/", ""))
                session.add(FoodLog(user_id=user_id, **ai['food_data']))
                await session.commit()
            except: pass
    return JSONResponse(content=await fetch_user_data(uid))

@app.post("/api/v1/user/{uid}/food/photo")
@app.post("/api/v1/user/{uid}/food/photo/")
async def add_food_photo(uid: str, file: UploadFile = File(...)):
    contents = await file.read()
    img_b64 = base64.b64encode(contents).decode('utf-8')
    ai = await process_food_chat("Analyze photo", photo_url=f"data:image/jpeg;base64,{img_b64}")
    if ai and ai.get('food_data'):
        async with async_session() as session:
            try:
                user_id = int(str(uid).replace("/", ""))
                session.add(FoodLog(user_id=user_id, **ai['food_data']))
                await session.commit()
            except: pass
    data = await fetch_user_data(uid)
    return JSONResponse(content={**data, "status": "ok", "food_data": ai.get('food_data')})

# --- COMPATIBILITY WITH WEB APP (Unified Endpoints) ---

class FoodAddRequest(BaseModel):
    text: Optional[str] = None
    image_base64: Optional[str] = None

@app.post("/api/user/{uid}/add_food")
async def add_food_unified(uid: str, data: FoodAddRequest):
    try:
        user_id = int(str(uid).replace("/", ""))
    except: return JSONResponse({"error": "invalid_id"}, 400)

    # 1. Prepare request for AI
    prompt = data.text or "Что на фото?"
    photo_url = None
    if data.image_base64:
        # Check if header exists
        if "data:image" in data.image_base64:
            photo_url = data.image_base64
        else:
            photo_url = f"data:image/jpeg;base64,{data.image_base64}"
    
    # 2. Call AI
    ai = await process_food_chat(prompt, photo_url=photo_url)
    
    # 3. Save if food found
    if ai and ai.get('food_data'):
        async with async_session() as session:
            # Check user exists first
            u_res = await session.execute(select(User).filter(User.id == user_id))
            if not u_res.scalar_one_or_none():
                session.add(User(id=user_id, daily_calorie_limit=2500))
                await session.commit()

            session.add(FoodLog(user_id=user_id, **ai['food_data']))
            await session.commit()
            
    # 4. Return updated stats
    return await fetch_user_data(uid)

@app.get("/api/user/{uid}/profile")
async def get_profile_unified(uid: str):
    try:
        user_id = int(str(uid).replace("/", ""))
    except: return JSONResponse({"error": "invalid_id"}, 400)

    async with async_session() as session:
        # Get User
        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
             user = User(id=user_id, balance=0, height=None, weight=None)
             session.add(user)
             await session.commit()
        
        # Get Nutrition Today
        today = datetime.utcnow().date()
        # Simple fetch of all time or filtered (MVP uses simple fetch for now to match logic)
        f_res = await session.execute(select(FoodLog).filter(FoodLog.user_id == user_id))
        all_logs = f_res.scalars().all()
        # Filter strictly for today to be correct? Let's sum ALL for visibility or just today.
        # Let's stick to Today for profile correctness if possible, or all if that was the plan.
        # User requested per-day reset. Let's filter by today.
        todays_logs = [l for l in all_logs if l.created_at.date() == today]

        total_cal = sum(l.calories for l in todays_logs)
        total_p = sum(l.protein or 0 for l in todays_logs)
        total_f = sum(l.fat or 0 for l in todays_logs)
        total_c = sum(l.carbs or 0 for l in todays_logs)

        return {
            "status": "ok",
            "profile": {
                "height": user.height,
                "weight": user.weight,
                "sport": user.sport,
                "gender": user.gender,
                "goal": user.goal,
                "balance": user.balance or 0,
                "daily_calorie_limit": user.daily_calorie_limit or 2500
            },
            "nutrition": {
                "total_calories": total_cal,
                "limit": user.daily_calorie_limit or 2500,
                "total_protein": total_p,
                "total_fat": total_f,
                "total_carbs": total_c
            }
        }
@app.post("/api/v1/user/{uid}/profile/")
async def update_profile(uid: str, request: Request):
    data = await request.json()
    user_id = int(str(uid).replace("/", ""))
    
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(content={"error": "user_not_found"}, status_code=404)
        
        # Update profile data
        if 'height' in data:
            user.height = data['height']
        if 'weight' in data:
            user.weight = data['weight']
        if 'age' in data:
            user.age = data['age']
        if 'gender' in data:
            user.gender = data['gender']
        if 'goal' in data:
            user.goal = data['goal']
        
        # Auto-calculate calorie and macro goals
        if user.weight and user.height and user.age:
            # Mifflin-St Jeor equation
            if user.gender == 'male':
                bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
            else:
                bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161
            
            # Activity factor (moderate)
            tdee = bmr * 1.55
            
            # Adjust for goal
            if user.goal == 'lose':
                calories = tdee - 500
            elif user.goal == 'gain':
                calories = tdee + 300
            else:
                calories = tdee
            
            user.daily_calorie_limit = int(calories)
            
            user.daily_calorie_limit = int(calories)
            
            # Macros calculated for response only (not saved to DB yet as columns missing)
            p_goal = int((calories * 0.30) / 4)
            f_goal = int((calories * 0.30) / 9)
            c_goal = int((calories * 0.40) / 4)
        
        await session.commit()
        
        return JSONResponse(content={
            "status": "ok",
            "calories": user.daily_calorie_limit,
            "protein": p_goal if 'p_goal' in locals() else 150,
            "fat": f_goal if 'f_goal' in locals() else 80,
            "carbs": c_goal if 'c_goal' in locals() else 250
        })

# --- STATICS ---
app.mount("/", StaticFiles(directory="web_app", html=True), name="static")

async def main():
    token = os.getenv("BOT_TOKEN")
    if token:
        bot = Bot(token=token); dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(user_handlers.router); dp.include_router(admin_handlers.router)
        asyncio.create_task(dp.start_polling(bot))
    port = int(os.getenv("PORT", 80))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    await uvicorn.Server(config).serve()

if __name__ == "__main__":
    asyncio.run(main())
