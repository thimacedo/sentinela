# scripts/run_auditoria_financeira.py
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

from workers.financial.sa_auditoria_financeira import SaAuditoriaFinanceira

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_auditoria_financeira")

async def main():
    logger.info("Disparando Subagente de Auditoria Financeira (SaAuditoriaFinanceira) sob demanda...")
    agent = SaAuditoriaFinanceira()
    res = await agent.run_financial_audit()
    logger.info(f"Auditoria concluída! Resultado: {res}")

if __name__ == "__main__":
    asyncio.run(main())
