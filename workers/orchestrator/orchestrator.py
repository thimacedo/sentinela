from __future__ import annotations
import asyncio
import logging
from typing import List
from workers.base.worker_base import BaseWorker
from workers.base.reward_engine import RewardEngine
from workers.base.memory_store import MemoryStore
from workers.ai.ai_advisor import AIAdvisor

logger = logging.getLogger("orchestrator")


class SentinelaOrchestrator:
    def __init__(self, reward_engine: RewardEngine, ai_advisor: AIAdvisor):
        self.reward_engine = reward_engine
        self.ai_advisor    = ai_advisor
        self._workers: List[BaseWorker] = []

    def register(self, worker: BaseWorker) -> None:
        self._workers.append(worker)
        logger.info(f"[orchestrator] registrado: {worker.worker_id}")

    async def run_all(self) -> None:
        if not self._workers:
            logger.warning("[orchestrator] Nenhum worker registrado.")
            return
        logger.info(f"[orchestrator] Iniciando {len(self._workers)} worker(s)...")
        tasks = [
            asyncio.create_task(
                worker.start(self.reward_engine, self.ai_advisor),
                name=worker.worker_id,
            )
            for worker in self._workers
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.stop_all()
            raise

    def stop_all(self) -> None:
        for w in self._workers:
            w.stop()
        logger.info(f"[orchestrator] Stop: {len(self._workers)} worker(s).")

    @property
    def worker_ids(self) -> List[str]:
        return [w.worker_id for w in self._workers]
