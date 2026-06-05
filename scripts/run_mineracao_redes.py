# scripts/run_mineracao_redes.py
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

from workers.analytics.sa_mineracao_redes import SaMineracaoRedes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_mineracao_redes")

async def main():
    logger.info("Disparando Subagente de Mineração de Redes (SaMineracaoRedes) sob demanda...")
    agent = SaMineracaoRedes()
    await agent.setup()
    try:
        res = await agent.run_analysis()
        logger.info(f"Análise concluída! Resultado: {res}")
    finally:
        await agent.teardown()

if __name__ == "__main__":
    asyncio.run(main())
