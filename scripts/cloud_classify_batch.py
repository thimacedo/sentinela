"""
Sentinela Cloud Classify Batch (v80.1)
Executa classificação em lote de comentários pendentes usando o AIService.
"""
from __future__ import annotations

import os
import sys
import logging
import asyncio

# --- Auto-Anchoring (PASA v80.1) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cloud_classify_batch")

async def main():
    logger.info("Iniciando processamento em lote da inteligência da Sentinela...")
    
    # Importação do AIService após ancoragem do diretório
    from core.ai_service import ai_service
    
    # Processa até 100 comentários por execução no workflow do Github Actions
    limit = 100
    try:
        processed_count = await ai_service.run_batch_classification(limit=limit)
        logger.info(f"Ciclo concluído. Total de comentários classificados nesta rodada: {processed_count}")
    except Exception as e:
        logger.error(f"Erro catastrófico no ciclo de classificação: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
