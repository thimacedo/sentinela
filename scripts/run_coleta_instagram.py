# scripts/run_coleta_instagram.py
import asyncio
import logging
import os
import sys
from pathlib import Path

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.scrapers.wk_coleta_instagram import WkColetaInstagram

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_coleta_instagram")

async def main():
    logger.info("Disparando Coletor de Instagram (WkColetaInstagram) sob demanda...")
    config = {
        "max_posts": int(os.getenv("MAX_POSTS_PER_PROFILE", "3")),
        "max_comments_per_post": int(os.getenv("MAX_COMMENTS_PER_POST", "50")),
        "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    }
    worker = WkColetaInstagram(worker_id="ig-v2-manual", config=config)
    await worker.setup()
    try:
        res = await worker.run_cycle()
        logger.info(f"Ciclo concluído! Resultado: {res}")
    finally:
        await worker.teardown()

if __name__ == "__main__":
    asyncio.run(main())
