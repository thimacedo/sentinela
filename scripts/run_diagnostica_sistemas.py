# scripts/run_diagnostica_sistemas.py
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

from workers.base.memory_store import MemoryStore
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.sa_diagnostica_sistemas import SaDiagnosticaSistemas
from workers.base.cycle_result import CycleResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_diagnostica_sistemas")

async def main():
    logger.info("Disparando Subagente SRE (SaDiagnosticaSistemas) sob demanda...")
    store = MemoryStore()
    fetcher = DocFetcher()
    advisor = SaDiagnosticaSistemas(memory=store, fetcher=fetcher)
    
    # Simula um resultado degradado/com falha para testes do Advisor
    logger.info("Simulando diagnóstico de falha para o worker ig-v2-01...")
    sim_result = CycleResult(
        worker_id="ig-v2-01",
        cycle=42,
        target="@candidato_teste",
        source="instagram_scraper",
        extracted=0,
        failed=1,
        error="WinError 10060: Uma tentativa de conexão falhou porque o componente conectado não respondeu",
        db_success=False,
        metadata={"duration_seconds": 15.4}
    )
    
    # Criamos um mock class com atributo worker_id
    class DummyWorker:
        def __init__(self, worker_id):
            self.worker_id = worker_id
    
    await advisor.analyze_and_suggest(DummyWorker("ig-v2-01"), sim_result)
    logger.info("Diagnóstico concluído! Verifique a tabela 'worker_suggestions' para ver a recomendação da IA.")

if __name__ == "__main__":
    asyncio.run(main())
