# scripts/run_doc_fetcher.py
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

from workers.ai.doc_fetcher import DocFetcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_doc_fetcher")

async def main():
    logger.info("Disparando Sincronizador de Documentos Técnicos (DocFetcher)...")
    fetcher = DocFetcher()
    await fetcher.refresh_all()
    logger.info("Sincronização concluída com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
