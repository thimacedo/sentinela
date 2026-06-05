from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
from typing import Optional
from workers.base.worker_base import BaseWorker

class BaseSubAgent(BaseWorker, ABC):
    """
    Abstração para subagentes analíticos efêmeros.
    Fornece mecanismos para offloading de CPU-bound (via ProcessPoolExecutor)
    e I/O-bound (via asyncio.to_thread).
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self._cpu_executor: Optional[ProcessPoolExecutor] = None

    async def setup(self) -> None:
        """Configura os recursos. Deve ser chamado no setup das subclasses."""
        self._cpu_executor = ProcessPoolExecutor(max_workers=2)
        self.logger.info(f"[{self.worker_id}] Subagente inicializado com ProcessPoolExecutor.")

    async def teardown(self) -> None:
        """Limpa os recursos. Deve ser chamado no teardown das subclasses."""
        if self._cpu_executor:
            self._cpu_executor.shutdown(wait=True)
            self._cpu_executor = None
        self.logger.info(f"[{self.worker_id}] Subagente encerrado e pools limpos.")

    async def run_cpu_bound(self, fn, *args):
        """Executa uma função síncrona de CPU-bound em um processo isolado."""
        if not self._cpu_executor:
            raise RuntimeError(f"[{self.worker_id}] ProcessPoolExecutor não inicializado. Chamou setup()?")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._cpu_executor, fn, *args)

    async def run_io_bound(self, fn, *args):
        """Executa uma função síncrona de I/O bloqueante em uma thread isolada."""
        return await asyncio.to_thread(fn, *args)
