import asyncio
from datetime import datetime
from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine


class FakeMetrics:
    def __init__(self, collected, failed, duration, errors):
        self.worker_id        = "teste-reward-001"
        self.cycle            = 1
        self.items_collected  = collected
        self.items_failed     = failed
        self.duration_seconds = duration
        self.errors           = errors
        self.timestamp        = datetime.utcnow()

    @property
    def success_rate(self):
        total = self.items_collected + self.items_failed
        return self.items_collected / total if total > 0 else 0.0

    @property
    def is_healthy(self):
        return self.success_rate >= 0.7 and len(self.errors) < 5


class FakeWorker:
    worker_id = "teste-reward-001"


async def main():
    store  = MemoryStore()
    engine = RewardEngine(store)
    worker = FakeWorker()

    casos = [
        ("Perfeito",    FakeMetrics(100, 0,  10.0, [])),
        ("Bom",         FakeMetrics(80,  10, 30.0, ["erro leve"])),
        ("Degradado",   FakeMetrics(20,  80, 90.0, ["e1","e2","e3","e4","e5"])),
        ("Zero",        FakeMetrics(0,   0,  0.0,  [])),
    ]

    for nome, metrics in casos:
        result = await engine.evaluate(worker, metrics)
        print(
            f"[{nome:10}] score={result.score:5.1f} "
            f"tier={result.tier:6} "
            f"badges={result.badges} "
            f"→ {result.recommendation}"
        )

    print("✅ reward_engine OK")


asyncio.run(main())
