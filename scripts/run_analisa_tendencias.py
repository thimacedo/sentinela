# scripts/run_analisa_tendencias.py
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

from workers.analytics.wk_analisa_tendencias import generate_trends

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_analisa_tendencias")

def main():
    logger.info("Disparando Analisador de Tendências (WkAnalisaTendencias) sob demanda...")
    try:
        out_path = generate_trends(days=7)
        logger.info(f"Relatório de tendências gerado em: {out_path}")
    except Exception as e:
        logger.error(f"Erro ao gerar tendências: {e}")

if __name__ == "__main__":
    main()
