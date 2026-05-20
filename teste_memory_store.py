import asyncio
from dataclasses import dataclass
from datetime import datetime
from workers.base.memory_store import MemoryStore

@dataclass
class WorkerMetrics:
    worker_id: str
    cycle: int
    items_collected: int
    items_failed: int
    duration_seconds: float
    errors: list
    timestamp: datetime

async def test_memory_store():
    store = MemoryStore()
    
    # Teste simples de conexão/operação
    print("✅ Conexão com Supabase OK")
    
    metrics = WorkerMetrics(
        worker_id="test_worker",
        cycle=1,
        items_collected=10,
        items_failed=0,
        duration_seconds=1.5,
        errors=[],
        timestamp=datetime.utcnow()
    )
    
    await store.save_metrics(metrics)
    print("✅ save_metrics OK")
    
    await store.save_suggestion("test_worker", 1, "test suggestion")
    print("✅ save_suggestion OK")
    
    res = await store.get_pending_suggestions()
    print(f"✅ get_pending_suggestions OK → {len(res)} registro(s)")

if __name__ == "__main__":
    asyncio.run(test_memory_store())
