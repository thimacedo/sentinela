import asyncio
import os
from core.ai_service import ai_service
from dotenv import load_dotenv

load_dotenv()

async def test():
    print(f"OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL')}")
    print(f"OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL')}")
    try:
        res = await ai_service.classify_text('Você é um idiota!')
        print(f"Resultado: {res}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    asyncio.run(test())
