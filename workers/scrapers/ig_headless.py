from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
import logging

class IGHeadlessWorker(BaseWorker):
    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.logger = logging.getLogger(f"worker.{worker_id}")
        self.cycle = 0

    def describe(self) -> str:
        return "Instagram Scraper via Playwright (Fallback)"

    async def setup(self) -> None:
        self.logger.info("Motor Headless configurado.")

    async def teardown(self) -> None:
        self.logger.info("Motor Headless encerrado.")

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        # Comportamento de Fallback/Dry-Run enquanto não integrado
        self.logger.info(f"Ciclo #{self.cycle}: Operando como fallback (Dry-Run)")
        
        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            source="fallback_headless",
            simulated=True,
            error="worker_not_integrated_with_real_scraper"
        )
