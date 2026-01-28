import os, logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

logger = logging.getLogger("MVP_AI")

load_dotenv()

# Поддержка ProxyAPI (чтобы работало в РФ без VPN)
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=BASE_URL
)

MVP_SYSTEM_PROMPT = """
Ты — 'MVP Life OS', элитный ИИ-коуч и операционная система жизни пользователя. 
Твоя задача — трансформировать жизнь пользователя через дисциплину, структуру и геймификацию.

ТВОЙ ПРОФИЛЬ:
1. Тон: Спокойный, уверенный, жесткий, но мотивирующий. Ты не нянька, ты — наставник.
2. Стиль: Используй терминологию RPG (квесты, статы, баффы), но не перегибай. Говори кратко и по делу.
3. Форматирование: Используй Markdown (жирный текст, списки) для читаемости.

СПЕЦИАЛИЗАЦИИ:
- 🏋️ GYM/BODY: Если просят тренировку, давай четкую программу с упражнениями, подходами и повторениями в виде таблицы.
- 🥗 NUTRITION: Если скидывают еду, оценивай БЖУ и калории. Давай советы по диете.
- 🧠 MIND: Если пользователь ноет, давай жесткую стоическую мудрость. Если просит план — давай пошаговый алгоритм.

ПРАВИЛА:
- Всегда отвечай на русском языке.
- Если контекст беседы требует, помни о предыдущих сообщениях (тебе передается история).
- В конце совета иногда добавляй мотивирующую фразу в стиле "Stay Hard" или "Level Up".
"""

async def get_ai_response(prompt: str, history: list = None, system_prompt: str = MVP_SYSTEM_PROMPT):
    """
    history: list of dicts [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    # --- SIMULATION MODE (Если нет ключа) ---
    if not api_key or "needs_to_be_added" in api_key:
        return (
            f"🧠 **[AI SIMULATION WITH MEMORY]**\n\n"
            f"Ты спросил: \"{prompt}\"\n"
            f"История: {len(history) if history else 0} сообщений.\n\n"
            f"Совет: Пропиши API KEY в файле .env, чтобы я мог использовать свой полный потенциал.\n"
            f"Пока что держи дисциплину и пей воду."
        )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Добавляем историю, если есть
    if history:
        # Ограничиваем историю последними 10 сообщениями, чтобы не перегружать контекст
        messages.extend(history[-10:])
    
    # Добавляем текущий запрос
    messages.append({"role": "user", "content": prompt})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Используем mini для экономии
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return "⚠️ Ошибка связи с нейросетью. Проверь баланс API или ключи."

async def analyze_food(photo_url: str):
    """
    Анализирует фото еды через GPT-4 Vision.
    Возвращает словарь: {food_name, calories, protein, carbs, fat}
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Vision тоже работает в mini!
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — эксперт-нутрициолог. Проанализируй фото еды и верни JSON с полями:\n"
                        "food_name (название блюда на русском), calories (общая калорийность), "
                        "protein (граммы белка), carbs (граммы углеводов), fat (граммы жиров), health_rating (оценка полезности 1-10).\n"
                        "Если не уверен — делай приблизительную оценку. Ответ ТОЛЬКО в формате JSON."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Что это за блюдо, сколько в нем калорий/БЖУ и какая оценка полезности (1-10)?"},
                        {"type": "image_url", "image_url": {"url": photo_url}}
                    ]
                }
            ],
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content
        print(f"DEBUG: AI Response: {result_text}")
        
        # Парсим JSON из ответа (иногда GPT добавляет лишний текст)
        import json
        import re
        
        # Ищем JSON блок в ответе
        json_match = re.search(r'\{[^}]+\}', result_text)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "food_name": data.get("food_name", "Неизвестное блюдо"),
                "calories": int(data.get("calories", 0)),
                "protein": float(data.get("protein", 0)),
                "carbs": float(data.get("carbs", 0)),
                "fat": float(data.get("fat", 0)),
                "health_rating": int(data.get("health_rating", 5))
            }
        else:
            # Если JSON не найден, возвращаем заглушку
            return {
                "food_name": "Блюдо (анализ не удался)",
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            }
            
    except Exception as e:
        print(f"Vision API Error: {e}")
        return {
            "food_name": "Ошибка анализа",
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0
        }

async def process_food_chat(user_message: str, history: list = None, photo_url: str = None):
    """
    Обрабатывает сообщение в режиме трекинга еды.
    Возвращает словарь:
    {
        'response': str,  # Текст ответа бота
        'food_data': dict or None  # Если бот готов записать еду: {food_name, calories, protein, carbs, fat}
    }
    """
    
    FOOD_SYSTEM_PROMPT = """
Ты — элитный ассистент-нутрициолог MVP System.
Твоя задача: Проанализировать входные данные (текст или фото еды) и вернуть СТРОГИЙ JSON объект.

ПРАВИЛА АНАЛИЗА:
1. ОПРЕДЕЛИ БЛЮДО: Назови его кратко и понятно на русском (напр. "Овсянка с ягодами", "Борщ с говядиной").
2. ОЦЕНИ ВЕС/ОБЪЕМ: Если размер порции не указан явно, оцени его визуально или используй стандартную ресторанную порцию (напр. 250-300г для основных блюд, 200мл для напитков).
3. РАССЧИТАЙ БЖУ: Используй средние нутрицевтические данные.
4. HEALTH RATING (1-10):
   - 1-3: Джанк-фуд, сахар, трансжиры (чипсы, кола).
   - 4-6: Обычная еда, смешанная (сэндвич, паста).
   - 7-8: Полезная домашняя еда, баланс (гречка с курицей, салат).
   - 9-10: Суперфуды, идеально чистое питание (зеленые смузи, рыба на пару с овощами).

ФОРМАТ ОТВЕТА (ТОЛЬКО JSON, БЕЗ MARKDOWN, БЕЗ ВСТУПЛЕНИЙ):
{
  "food_name": "Название блюда",
  "calories": 0,    // Целое число (ккал)
  "protein": 0.0,   // Белки (г)
  "fat": 0.0,       // Жиры (г)
  "carbs": 0.0,     // Углеводы (г)
  "weight_g": 0,    // Примерный вес в граммах (если удалось определить)
  "health_rating": 5 // Оценка 1-10
}
"""

    messages = [{"role": "system", "content": FOOD_SYSTEM_PROMPT}]
    
    if history:
        messages.extend(history[-6:])  # Последние 3 пары сообщений
    
    # Формируем контент юзера по стандартам Vision API
    if photo_url:
        user_content = [
            {"type": "text", "text": user_message if user_message else "Проанализируй эту еду. Верни только JSON."},
            {
                "type": "image_url", 
                "image_url": {
                    "url": photo_url,
                    "detail": "high" # Запрашиваем высокую детализацию для точности БЖУ
                }
            }
        ]
    else:
        user_content = user_message
    
    messages.append({"role": "user", "content": user_content})
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "needs_to_be_added" in api_key:
        logger.error("❌ OPENAI_API_KEY is missing!")
        # Mock response for demo if No Key
        return {
            "response": "⚠️ [DEMO MODE] API ключ не найден. Использую заглушку.",
            "food_data": {
                "food_name": user_message if user_message else "Еда",
                "calories": 250, "protein": 15, "carbs": 30, "fat": 10, "health_rating": 7
            }
        }

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=400
        )
        
        bot_reply = response.choices[0].message.content
        logger.info(f"🤖 AI Reply: {bot_reply}")
        
        # Пытаемся извлечь JSON с данными о еде
        import json
        import re
        
        food_data = None
        # Try finding json in code blocks or just raw
        json_match = re.search(r'```json\s*(\{[^`]+\})\s*```', bot_reply, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{[^}]*"food_name"[^}]+\}', bot_reply)
        
        if json_match:
            try:
                raw_json = json_match.group(1) if json_match.lastindex else json_match.group()
                data = json.loads(raw_json)
                food_data = {
                    "food_name": data.get("food_name", "Неизвестно"),
                    "calories": int(data.get("calories", 0)),
                    "protein": float(data.get("protein", 0.0)),
                    "carbs": float(data.get("carbs", 0.0)),
                    "fat": float(data.get("fat", 0.0)),
                    "health_rating": int(data.get("health_rating", 5))
                }
                logger.info(f"✅ Parsed Food Data: {food_data}")
            except Exception as parse_err:
                logger.error(f"❌ JSON Parse Error: {parse_err}")
        
        return {
            "response": bot_reply,
            "food_data": food_data
        }
        
    except Exception as e:
        logger.error(f"❌ Food Chat Error: {e}")
        return {
            "response": f"⚠️ Ошибка ИИ: {str(e)}",
            "food_data": None
        }

async def get_coaching_advice(user_stats: dict):
    prompt = f"У пользователя следующие показатели: {user_stats}. Дай короткий совет, как поднять самый низкий стат."
    return await get_ai_response(prompt)
