import asyncio
import os
from dotenv import load_dotenv

load_dotenv(override=True)

import sys
sys.path.append(os.getcwd())
from core.ai_service import ai_service

async def main():
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"GEMINI_API_KEY: {api_key[:5] if api_key else 'None'}...")
        result = await ai_service.classify_text("Isso é um teste de ódio. Eu odeio vocês todos.")
        print(result)
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main())
