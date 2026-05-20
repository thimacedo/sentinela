import asyncio
import logging
from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor
from workers.scrapers.ig_zyte import IGZyteWorker

async def run_full_pipeline():
    logging.basicConfig(level=logging.INFO)
    print("--- 🚀 INICIANDO TESTE REAL DE PISTA DE PONTAS ---")
    
    # Setup
    memory = MemoryStore()
    reward = RewardEngine(memory)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory, fetcher)
    worker = IGZyteWorker("ig-zyte-prod-01", {})
    
    # 1. Ciclo de Coleta
    print("[1/3] Coletando dados reais...")
    await worker.setup()
    metrics = await worker.run_cycle()
    print(f"✅ Coleta finalizada: {metrics.items_collected} itens.")
    
    # 2. Avaliação de Recompensa
    print("[2/3] Avaliando performance...")
    reward_result = await reward.evaluate(worker, metrics)
    print(f"✅ Recompensa: Score {reward_result.score} (Tier: {reward_result.tier})")
    
    # 3. Auditoria/Advisor
    print("[3/3] Auditoria de IA...")
    if reward_result.score < 50:
        await advisor.analyze_and_suggest(worker, metrics)
        print("✅ Sugestão de IA gerada e salva.")
    else:
        print("✅ Performance estável, advisor não acionado.")
        
    await worker.teardown()
    print("--- 🏁 TESTE FINALIZADO COM SUCESSO ---")

if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
