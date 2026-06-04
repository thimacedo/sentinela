import asyncio
import logging
import os
import sys
import time

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(override=True)

from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor
from workers.orchestrator.orchestrator import SentinelaOrchestrator
from workers.scrapers.instagram_worker import InstagramWorker
from workers.processors.ai_processor_worker import AIProcessorWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Test_5Min")

async def run_5min_test():
    logger.info("=== INICIANDO TESTE DE 5 MINUTOS (COLETA E CLASSIFICAÇÃO) ===")
    
    store = MemoryStore()
    engine = RewardEngine(store)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory=store, fetcher=fetcher)
    orch = SentinelaOrchestrator(engine, advisor)

    # Configurando os workers
    scraper_worker = InstagramWorker(
        worker_id="ig-test-01",
        config={"max_posts": 2, "max_comments_per_post": 10, "headless": True}
    )
    ai_worker = AIProcessorWorker(
        worker_id="ai-test-01",
        config={"batch_size": 20}
    )

    orch.register(scraper_worker)
    orch.register(ai_worker)

    orch.shutdown_event = asyncio.Event()

    start_time = time.time()
    test_duration = 300  # 5 minutos

    async def custom_worker_loop(worker, is_scraper):
        while time.time() - start_time < test_duration:
            if orch.shutdown_event.is_set():
                break
            
            logger.info(f"--- Iniciando ciclo de teste para {worker.worker_id} ---")
            try:
                # Usa run_cycle direto ou via orquestrador
                await orch.run_cycle_with_validation_v2(worker)
            except Exception as e:
                logger.error(f"Erro no ciclo do {worker.worker_id}: {e}")
            
            # Pequeno intervalo para não sobrecarregar e permitir intercalação
            sleep_time = 10 if is_scraper else 5
            logger.info(f"--- Ciclo do {worker.worker_id} finalizado. Aguardando {sleep_time}s ---")
            await asyncio.sleep(sleep_time)

    # Executa os loops
    try:
        await asyncio.gather(
            custom_worker_loop(scraper_worker, is_scraper=True),
            custom_worker_loop(ai_worker, is_scraper=False),
        )
    except asyncio.CancelledError:
        pass
    finally:
        logger.info("=== TESTE DE 5 MINUTOS CONCLUÍDO ===")
        orch.stop_all()

if __name__ == "__main__":
    asyncio.run(run_5min_test())
