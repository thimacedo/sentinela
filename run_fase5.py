import asyncio
import logging
from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.advisor import AIAdvisor
from workers.scrapers.ig_headless import IGHeadlessWorker
from workers.scrapers.ig_zyte import IGZyteWorker
from workers.orchestrator import SentinelaOrchestrator

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Setup
    memory = MemoryStore()
    reward = RewardEngine(memory)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory, fetcher)
    
    orch = SentinelaOrchestrator(reward, advisor)
    
    # Registro
    orch.register_worker(IGHeadlessWorker("ig-headless-01", {}))
    orch.register_worker(IGZyteWorker("ig-zyte-01", {}))
    
    # Execução (com timeout para teste)
    print("✅ Orquestrador configurado. Iniciando teste de 5 segundos...")
    try:
        await asyncio.wait_for(orch.run_all(), timeout=5.0)
    except asyncio.TimeoutError:
        print("✅ Orquestrador executou o loop com sucesso.")
        orch.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
