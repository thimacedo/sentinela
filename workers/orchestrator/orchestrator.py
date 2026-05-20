from __future__ import annotations
import asyncio
import logging
from typing import List
from workers.base.worker_base import BaseWorker
from workers.base.reward_engine import RewardEngine
from workers.base.memory_store import MemoryStore
from workers.ai.ai_advisor import AIAdvisor
from workers.base.cycle_result import CycleResult

logger = logging.getLogger("orchestrator")


class SentinelaOrchestrator:
    def __init__(self, reward_engine: RewardEngine, ai_advisor: AIAdvisor):
        self.reward_engine = reward_engine
        self.ai_advisor    = ai_advisor
        self._workers: List[BaseWorker] = []

    def register(self, worker: BaseWorker) -> None:
        self._workers.append(worker)
        logger.info(f"[orchestrator] registrado: {worker.worker_id}")

    async def run_cycle_with_validation(self, worker: BaseWorker) -> None:
        # Executa um único ciclo do worker
        result = await worker.run_cycle()
        
        if not isinstance(result, CycleResult):
            logger.warning(
                "[orchestrator] %s retornou resultado inválido. Marcando como simulado.",
                worker.worker_id,
            )
            result = CycleResult(
                worker_id=worker.worker_id,
                cycle=getattr(worker, "cycle", 0),
                simulated=True,
                error="worker_returned_invalid_result",
            )
            
        db_status = "n/a" if result.simulated else ("ok" if result.db_success else "falhou")
        ia_status = "n/a" if result.simulated else ("ok" if result.classifier_success else "nao")
            
        logger.info(
            "[%s] ciclo #%s | target=%s | origem=%s | extraidos=%s | inseridos=%s | "
            "duplicados=%s | classificados=%s | falhas=%s | db=%s | ia=%s | simulado=%s | erro=%s",
            result.worker_id,
            result.cycle,
            result.target or "N/A",
            result.source or "N/A",
            result.extracted,
            result.inserted,
            result.duplicated,
            result.classified,
            result.failed,
            db_status,
            ia_status,
            result.simulated,
            result.error or "nenhum",
        )
        
        # O RewardEngine agora processa o contrato CycleResult
        await self.reward_engine.process_result(result)
        
        if not result.simulated:
            await self.ai_advisor.analyze_and_suggest(worker, result)
        else:
            logger.debug("[%s] AIAdvisor ignorado (ciclo simulado)", worker.worker_id)

    async def run_all(self) -> None:
        if not self._workers:
            logger.warning("[orchestrator] Nenhum worker registrado.")
            return
        logger.info(f"[orchestrator] Iniciando {len(self._workers)} worker(s)...")
        # Ciclo orquestrado
        while True:
            await asyncio.gather(*(self.run_cycle_with_validation(w) for w in self._workers))
            await asyncio.sleep(60)

    def stop_all(self) -> None:
        for w in self._workers:
            w.stop()
        logger.info(f"[orchestrator] Stop: {len(self._workers)} worker(s).")

    @property
    def worker_ids(self) -> List[str]:
        return [w.worker_id for w in self._workers]
