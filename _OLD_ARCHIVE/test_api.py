"""
Quick test script to check if ProxyAPI is working
"""
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test_api():
    from openai import AsyncOpenAI
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    print(f"🔑 API Key: {api_key[:20]}..." if api_key else "❌ NO API KEY!")
    print(f"🌐 Base URL: {base_url}")
    
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    try:
        print("\n⏳ Testing API...")
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Скажи 'работает' одним словом"}],
            max_tokens=10
        )
        print(f"✅ SUCCESS: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
