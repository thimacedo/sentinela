# scripts/run_gera_alertas.py
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

from workers.processors.wk_gera_alertas import WkGeraAlertas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_gera_alertas")

async def main():
    logger.info("Disparando Monitor de Alertas (WkGeraAlertas) sob demanda...")
    worker = WkGeraAlertas(worker_id="alert-worker-manual", config={})
    await worker.setup()
    try:
        res = await worker.run_cycle()
        logger.info(f"Ciclo concluído! Resultado: {res}")
    finally:
        await worker.teardown()

if __name__ == "__main__":
    asyncio.run(main())
