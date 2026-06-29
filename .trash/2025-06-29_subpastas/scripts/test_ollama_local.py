import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())
from core.ai_service import ai_service
import logging

logging.basicConfig(level=logging.DEBUG)

async def test():
    try:
        res = await ai_service.classify_text('test', '123')
        print(f"RESULT: {res}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
