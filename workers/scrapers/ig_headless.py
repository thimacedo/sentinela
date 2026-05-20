from workers.base.worker_base import BaseWorker, WorkerMetrics
import asyncio

class IGHeadlessWorker(BaseWorker):
    def describe(self) -> str:
        return "Instagram Headless via Playwright"

    async def setup(self) -> None:
        self.logger.info("Setup Playwright...")

    async def run_cycle(self) -> WorkerMetrics:
        self.logger.info("Executando coleta headless...")
        # Simula coleta real
        await asyncio.sleep(1)
        return WorkerMetrics(self.worker_id, self.cycle, items_collected=5, duration_seconds=1.2)

    async def teardown(self) -> None:
        self.logger.info("Teardown Playwright...")
