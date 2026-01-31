from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from database.db_helper import async_session
from database.models import User, Task
from sqlalchemy import select, delete
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем запросы от Web App (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskSync(BaseModel):
    id: Optional[str] = None
    text: str
    completed: bool
    category: str
    isRitual: bool

class SyncRequest(BaseModel):
    user_id: int
    tasks: List[TaskSync]

class ProfileUpdateRequest(BaseModel):
    user_id: int
    height: Optional[int] = None
    weight: Optional[float] = None
    sport: Optional[str] = None
    gender: Optional[str] = None
    goal: Optional[str] = None

@app.post("/update_profile")
async def update_profile(data: ProfileUpdateRequest):
    async with async_session() as session:
        user_result = await session.execute(select(User).filter(User.id == data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            # Create if not exists (lazy init)
            user = User(id=data.user_id)
            session.add(user)
        
        if data.height is not None: user.height = data.height
        if data.weight is not None: user.weight = data.weight
        if data.sport is not None: user.sport = data.sport
        if hasattr(data, 'gender') and data.gender is not None: user.gender = data.gender
        if hasattr(data, 'goal') and data.goal is not None: user.goal = data.goal
        
        # Recalculate Calories (Mifflin-St Jeor Equation)
        age = 25 
        w = user.weight or 75
        h = user.height or 175
        gender_coeff = 5 if user.gender == 'male' else -161
        activity_mult = 1.2 # Sedentary
        
        # Activity Multipliers
        sport_map = {
            'none': 1.2,
            'gym': 1.55,
            'basketball': 1.6,
            'boxing': 1.7,
            'football': 1.6,
            'wrestling': 1.7
        }
        activity_mult = sport_map.get(user.sport, 1.2)
            
        bmr = (10 * w) + (6.25 * h) - (5 * age) + gender_coeff
        tdee = bmr * activity_mult
        
        # Goal Adjustment
        target_calories = tdee
        if user.goal == 'lose':
            target_calories = tdee * 0.80 # -20%
        elif user.goal == 'gain':
            target_calories = tdee * 1.15 # +15%
            
        user.daily_calorie_limit = int(target_calories)

        await session.commit()
        
        # Calculate current consumed (Simple generic sum for MVP, ideally filter by date)
        # Re-fetching user with logs to ensure fresh data
        # Note: In a real app, filter by DATE(now). Here we take all for simplicity or assume cleanup.
        # Actually, let's just sum what we have access to or return 0 and let client re-fetch history.
        # Better: let's do a quick query for today's stats if possible, or just sum all for now.
        
        # Calculate current consumed & macros
        total_cal_today = 0
        total_p = 0
        total_f = 0
        total_c = 0
        
        if user.food_logs:
            # Simple sum of all logs for this user (MVP simplification) or filter logic if implemented
            total_cal_today = sum([l.calories for l in user.food_logs])
            total_p = sum([l.protein or 0 for l in user.food_logs])
            total_f = sum([l.fat or 0 for l in user.food_logs])
            total_c = sum([l.carbs or 0 for l in user.food_logs])

        return {
            "status": "success", 
            "new_limit": user.daily_calorie_limit, 
            "current_total": total_cal_today,
            "stats": {
                "total_calories": total_cal_today,
                "limit": user.daily_calorie_limit,
                "total_protein": total_p,
                "total_fat": total_f,
                "total_carbs": total_c
            }
        }

@app.post("/sync_tasks")
async def sync_tasks(data: SyncRequest):
    async with async_session() as session:
        # Проверяем юзера
        user_result = await session.execute(select(User).filter(User.id == data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
             user = User(id=data.user_id)
             session.add(user)
             await session.flush()

        # Простой способ синхронизации для MVP: 
        # Удаляем старые задачи за сегдня и записываем новые
        await session.execute(delete(Task).filter(Task.user_id == data.user_id))
        
        for t in data.tasks:
            new_task = Task(
                user_id=data.user_id,
                title=t.text,
                category=t.category,
                is_ritual=t.isRitual,
                is_completed=t.completed
            )
            session.add(new_task)
        
        await session.commit()
        return {"status": "success", "message": f"Synced {len(data.tasks)} tasks"}

@app.get("/get_stats/{user_id}")
async def get_stats(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Task).filter(Task.user_id == user_id))
        tasks = result.scalars().all()
        
        total = len(tasks)
        completed = len([t for t in tasks if t.is_completed])
        
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }

@app.get("/api/user/{user_id}/profile")
async def get_full_profile(user_id: int):
    async with async_session() as session:
        # 1. Get User Data
        result = await session.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
             # Lazy create if new
             user = User(id=user_id, balance=0, height=175, weight=75) # defaults
             session.add(user)
             await session.commit()
             # Re-fetch or just use defaults
        
        # 2. Get Today's Nutrition (Simple Sum)
        from database.models import FoodLog
        f_res = await session.execute(select(FoodLog).filter(FoodLog.user_id == user_id))
        all_logs = f_res.scalars().all()
        
        # Filter for "today" in real app, here for MVP we might sum all or just latest
        # Ideally, we should filter by date. For MVP v1, let's sum all to keep persistence visible.
        # IMPROVEMENT: If you want daily reset, we need date logic. 
        # For now, let's return ALL nutritional history sum as "Current State"
        
        total_cal = sum([l.calories for l in all_logs])
        total_p = sum([l.protein or 0 for l in all_logs])
        total_f = sum([l.fat or 0 for l in all_logs])
        total_c = sum([l.carbs or 0 for l in all_logs])

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

# --- FOOD ENDPOINTS ---
from database.models import FoodLog

class FoodAddRequest(BaseModel):
    text: Optional[str] = ""
    image_base64: Optional[str] = None # Base64 encoded image string

@app.post("/api/user/{user_id}/add_food")
async def add_food(user_id: int, data: FoodAddRequest):
    async with async_session() as session:
        # 1. Get User
        user = (await session.execute(select(User).filter(User.id == user_id))).scalar_one_or_none()
        if not user:
            user = User(id=user_id)
            session.add(user)
            await session.commit()
        
        # 2. Prepare AI Request
        from openai import AsyncOpenAI
        import os
        import json

        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        messages = [
            {
                "role": "system", 
                "content": "You are a nutritional AI. Identify the food. Return JSON: {\"food_name\": str, \"calories\": int, \"protein\": int, \"fat\": int, \"carbs\": int}. If unclear, estimate. Keep calories realistic."
            }
        ]

        user_content = []
        if data.text:
            user_content.append({"type": "text", "text": f"Analyze this food context: {data.text}"})
        
        if data.image_base64:
            # OPTIMIZATION: "detail": "low" costs fixed 85 tokens (~$0.00001) per image
            image_url = f"data:image/jpeg;base64,{data.image_base64}" if not data.image_base64.startswith("data:") else data.image_base64
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": "low" 
                }
            })
        
        if not user_content:
             return {"status": "error", "message": "No data provided"}

        messages.append({"role": "user", "content": user_content})

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            ai_content = response.choices[0].message.content
            # Cleanup code blocks
            ai_content = ai_content.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(ai_content)
            
            # Extract Data
            food_name = parsed_data.get("food_name", "Unknown Food")
            if data.text and len(data.text) < 20 and "Unknown" in food_name:
                food_name = data.text # Fallback to user text if AI failed to name it but counted cals
                
            cal = int(parsed_data.get("calories", 0))
            prot = int(parsed_data.get("protein", 0))
            fat = int(parsed_data.get("fat", 0))
            carbs = int(parsed_data.get("carbs", 0))

        except Exception as e:
            print(f"AI Error: {e}")
            return {"status": "error", "message": "AI processing failed"}

        # 3. Save Log
        new_log = FoodLog(
            user_id=user_id,
            food_name=food_name,
            calories=cal,
            protein=prot,
            fat=fat,
            carbs=carbs
        )
        session.add(new_log)
        await session.commit()
        
        # 4. Stats Recalculation (Reliable Sum)
        result = await session.execute(select(FoodLog).filter(FoodLog.user_id == user.id))
        all_logs = result.scalars().all()
        
        total_cal = sum([l.calories for l in all_logs])
        
        return {
            "status": "ok",
            "food_data": {
                "food_name": food_name,
                "calories": cal,
                "protein": prot,
                "fat": fat,
                "carbs": carbs
            },
            "stats": {
                "total_calories": total_cal,
                "limit": user.daily_calorie_limit or 2000,
                "total_protein": sum([l.protein or 0 for l in all_logs]),
                "total_fat": sum([l.fat or 0 for l in all_logs]),
                "total_carbs": sum([l.carbs or 0 for l in all_logs])
            }
        }

@app.get("/admin/global_stats")
async def global_stats():
    async with async_session() as session:
        user_count = await session.execute(select(User))
        users = len(user_count.scalars().all())
        
        task_count = await session.execute(select(Task))
        tasks = len(task_count.scalars().all())
        
        return {
            "total_users": users,
            "total_tasks_recorded": tasks
        }

# --- STATICS ---
# Must be last to not override API
app.mount("/", StaticFiles(directory="web_app", html=True), name="static")

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_api()
