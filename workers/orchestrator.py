import asyncio
import logging
from typing import List
from workers.base.worker_base import BaseWorker
from workers.base.reward_engine import RewardEngine
from workers.ai.advisor import AIAdvisor

class SentinelaOrchestrator:
    """
    Orquestrador central do ecossistema.
    Gerencia múltiplos workers e garante que todos estejam sob a tutela do AIAdvisor.
    """
    def __init__(self, reward_engine: RewardEngine, ai_advisor: AIAdvisor):
        self.reward_engine = reward_engine
        self.ai_advisor = ai_advisor
        self.workers: List[BaseWorker] = []
        self.logger = logging.getLogger("Orchestrator")

    def register_worker(self, worker: BaseWorker):
        self.workers.append(worker)
        self.logger.info(f"Worker {worker.worker_id} registrado.")

    async def run_all(self):
        """Inicia todos os workers registrados simultaneamente."""
        tasks = [
            worker.start(self.reward_engine, self.ai_advisor) 
            for worker in self.workers
        ]
        self.logger.info(f"Iniciando {len(tasks)} workers...")
        await asyncio.gather(*tasks)

    def stop_all(self):
        """Sinaliza parada para todos."""
        for worker in self.workers:
            worker.stop()
