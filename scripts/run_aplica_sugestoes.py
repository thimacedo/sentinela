# scripts/run_aplica_sugestoes.py
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

from workers.ai.wk_aplica_sugestoes import WkAplicaSugestoes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_aplica_sugestoes")

async def main():
    logger.info("Disparando Aplicador de Sugestões (WkAplicaSugestoes) sob demanda...")
    worker = WkAplicaSugestoes()
    try:
        await worker._process_pending_suggestions()
        logger.info("Verificação e aplicação de sugestões concluída!")
    except Exception as e:
        logger.error(f"Erro no processador de sugestões: {e}")

if __name__ == "__main__":
    asyncio.run(main())
