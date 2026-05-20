import asyncio
import os
import logging
from dotenv import load_dotenv
from workers.scrapers.ig_zyte import IGZyteWorker, Target
from workers.base.reward_engine import RewardEngine
from workers.base.memory_store import MemoryStore
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor
from workers.orchestrator.orchestrator import SentinelaOrchestrator

# Configuração de Logging para captura de evidências
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("validation_runtime")

async def run_single_validation_cycle():
    load_dotenv()
    
    # Setup infraestrutura mínima
    store = MemoryStore()
    engine = RewardEngine(store)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory=store, fetcher=fetcher)
    orch = SentinelaOrchestrator(engine, advisor)
    
    worker_id = "ig-zyte-val-02"
    config = {"max_posts": 1}
    worker = IGZyteWorker(worker_id, config)
    
    orch.register(worker)
    await worker.setup()
    
    logger.info("🚀 INICIANDO CICLO DE VALIDAÇÃO EM RUNTIME (Tentativa 2)")
    
    # Lista de alvos para tentar sucesso real
    potential_targets = ["gleisihoffmann", "pythonlearning", "instagram"]
    
    success = False
    for username in potential_targets:
        logger.info(f"Tentando alvo: @{username}")
        target = Target(username=username, source="validation_test")
        worker.claim_next_target = lambda: target
        
        await orch.run_cycle_with_validation(worker)
        
        # Verifica se o último resultado teve extração
        # Nota: O orchestrator não retorna o resultado, mas o reward engine o processa.
        # Vamos assumir que se falhar, tentamos o próximo.
        # (Neste script simplificado, ele vai rodar os 3 ciclos)
    
    await worker.teardown()
    logger.info("🏁 CICLO DE VALIDAÇÃO CONCLUÍDO")

if __name__ == "__main__":
    asyncio.run(run_single_validation_cycle())
