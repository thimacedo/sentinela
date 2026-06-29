# scripts/run_sa_instagram_stealth.py
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

from workers.ai.sa_instagram_stealth import SaInstagramStealth

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_sa_instagram_stealth")

async def main():
    logger.info("Disparando Subagente Instagram Stealth sob demanda...")
    config = {
        "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
        "use_proxy": True
    }
    worker = SaInstagramStealth(worker_id="sa-ig-stealth-manual", config=config)
    await worker.setup()
    try:
        res = await worker.run_cycle()
        logger.info(f"Ciclo concluído! Resultado: {res}")
    finally:
        await worker.teardown()
        
    input("Pressione ENTER para fechar a janela...")

if __name__ == "__main__":
    asyncio.run(main())
