import asyncio
from workers.base.memory_store import MemoryStore
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor

class FakeWorker:
    worker_id = "instagram-worker-01"

class FakeMetrics:
    cycle = 5

async def test_advisor():
    memory = MemoryStore()
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory, fetcher)
    worker = FakeWorker()
    metrics = FakeMetrics()

    # Execução
    await advisor.analyze_and_suggest(worker, metrics)
    
    # Validação
    pending = await memory.get_pending_suggestions()
    assert len(pending) > 0, "Falha: Sugestão não salva"
    print(f"✅ AIAdvisor: Sugestão salva → '{pending[0]['suggestion']}'")

if __name__ == "__main__":
    asyncio.run(test_advisor())
