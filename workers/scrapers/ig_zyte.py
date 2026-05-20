from workers.base.worker_base import BaseWorker, WorkerMetrics
import asyncio

class IGZyteWorker(BaseWorker):
    def describe(self) -> str:
        return "Instagram Scraper via Zyte API"

    async def setup(self) -> None:
        self.logger.info("Configurando motor Zyte...")

    async def run_cycle(self) -> WorkerMetrics:
        self.logger.info("Coletando via Zyte API...")
        await asyncio.sleep(0.5)
        return WorkerMetrics(self.worker_id, self.cycle, items_collected=12, duration_seconds=0.8)

    async def teardown(self) -> None:
        self.logger.info("Encerrando motor Zyte...")
