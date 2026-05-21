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
        self.reward_engine  = reward_engine
        self.ai_advisor     = ai_advisor
        self._workers: List[BaseWorker] = []
        # Alvos reservados no ciclo atual — compartilhado entre workers
        self._active_targets: set = set()
        self._claim_lock = asyncio.Lock()

    def register(self, worker: BaseWorker) -> None:
        self._workers.append(worker)
        logger.info("[orchestrator] registrado: %s", worker.worker_id)

    async def run_cycle_with_validation(self, worker: BaseWorker) -> None:
        # Injeta o set compartilhado antes do claim para evitar alvos duplicados
        worker.active_targets = self._active_targets
        worker.claim_lock = self._claim_lock

        result = await worker.run_cycle()

        if not isinstance(result, CycleResult):
            logger.warning(
                "[orchestrator] %s retornou resultado invalido. Marcando como simulado.",
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

        await self.reward_engine.process_result(result)

        if not result.simulated:
            await self.ai_advisor.analyze_and_suggest(worker, result)
        else:
            logger.debug("[%s] AIAdvisor ignorado (ciclo simulado)", worker.worker_id)

    async def run_all(self) -> None:
        if not self._workers:
            logger.warning("[orchestrator] Nenhum worker registrado.")
            return
        logger.info("[orchestrator] Iniciando %s worker(s)...", len(self._workers))
        while True:
            # Limpa alvos ativos a cada rodada
            self._active_targets.clear()
            await asyncio.gather(*(self.run_cycle_with_validation(w) for w in self._workers))
            await asyncio.sleep(60)

    def stop_all(self) -> None:
        for w in self._workers:
            w.stop()
        logger.info("[orchestrator] Stop: %s worker(s).", len(self._workers))

    @property
    def worker_ids(self) -> List[str]:
        return [w.worker_id for w in self._workers]
