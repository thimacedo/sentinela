from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workers.base.reward_engine import RewardEngine
    from workers.base.memory_store import MemoryStore


@dataclass
class WorkerMetrics:
    worker_id:        str
    cycle:            int
    items_collected:  int   = 0
    items_failed:     int   = 0
    duration_seconds: float = 0.0
    errors:           list[str] = field(default_factory=list)
    timestamp:        datetime  = field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        total = self.items_collected + self.items_failed
        return self.items_collected / total if total > 0 else 0.0

    @property
    def is_healthy(self) -> bool:
        return self.success_rate >= 0.7 and len(self.errors) < 5


class BaseWorker(ABC):
    """
    Contrato base para todos os workers do Sentinela.

    Ciclo de vida:
      setup() → run_cycle() [loop] → teardown()

    Regras:
      - Nunca sobrescrever o método start()
      - run_cycle() deve retornar WorkerMetrics mesmo em falha parcial
      - teardown() deve sempre liberar recursos, mesmo após exceção
    """

    def __init__(self, worker_id: str, config: dict):
        self.worker_id            = worker_id
        self.config               = config
        self.cycle                = 0
        self.is_running           = False
        self._consecutive_failures = 0
        self.logger               = logging.getLogger(f"worker.{worker_id}")

    # ── Contrato obrigatório ──────────────────────────────────────────────────

    @abstractmethod
    async def setup(self) -> None:
        """Inicialização de recursos (browser, sessão HTTP, etc)."""
        ...

    @abstractmethod
    async def run_cycle(self) -> "CycleResult":
        """
        Um ciclo completo de coleta.
        Deve retornar CycleResult mesmo em caso de falha parcial.
        """
        ...

    @abstractmethod
    async def teardown(self) -> None:
        """Limpeza de recursos. Sempre executado, mesmo após exceção."""
        ...

    @abstractmethod
    def describe(self) -> str:
        """Descrição legível do worker para logs e AIAdvisor."""
        ...

    # ── Loop autônomo gerenciado ──────────────────────────────────────────────

    async def start(
        self,
        reward_engine: RewardEngine,
        ai_advisor,
        interval_seconds: int = 300,
    ) -> None:
        """
        Loop autônomo — não requer supervisão externa.
        Avalia performance após cada ciclo e solicita IA se degradado.
        """
        self.is_running = True
        self.logger.info(f"[{self.worker_id}] Iniciando — {self.describe()}")

        await self.setup()

        try:
            while self.is_running:
                self.cycle += 1
                self.logger.info(f"[{self.worker_id}] Ciclo #{self.cycle} iniciado")

                try:
                    metrics = await self.run_cycle()
                    reward  = await reward_engine.evaluate(self, metrics)

                    self.logger.info(
                        f"[{self.worker_id}] Ciclo #{self.cycle} completo | "
                        f"score={reward.score:.1f} tier={reward.tier} | "
                        f"coletados={metrics.items_collected} "
                        f"taxa={metrics.success_rate:.0%}"
                    )

                    if reward.badges:
                        self.logger.info(f"[{self.worker_id}] Badges: {reward.badges}")

                    # Solicita análise se degradado
                    if reward.score < 40 or self._consecutive_failures >= 3:
                        self.logger.warning(
                            f"[{self.worker_id}] Degradado (score={reward.score:.1f}, "
                            f"falhas={self._consecutive_failures}) — acionando AIAdvisor"
                        )
                        await ai_advisor.analyze_and_suggest(self, metrics)
                        self._consecutive_failures = 0
                    elif not metrics.is_healthy:
                        self._consecutive_failures += 1
                    else:
                        self._consecutive_failures = 0

                    # Intervalo dinâmico baseado no tier
                    interval = reward_engine.get_interval(reward.tier)
                    self.logger.info(
                        f"[{self.worker_id}] Próximo ciclo em {interval}s (tier={reward.tier})"
                    )
                    await asyncio.sleep(interval)

                except asyncio.CancelledError:
                    self.logger.info(f"[{self.worker_id}] Ciclo cancelado.")
                    raise

                except Exception as e:
                    self._consecutive_failures += 1
                    self.logger.error(
                        f"[{self.worker_id}] Erro no ciclo #{self.cycle}: {e}",
                        exc_info=True,
                    )
                    await asyncio.sleep(interval_seconds)

        finally:
            self.logger.info(f"[{self.worker_id}] Encerrando teardown...")
            await self.teardown()
            self.logger.info(f"[{self.worker_id}] Encerrado.")

    def stop(self) -> None:
        """Sinaliza parada do loop no próximo ciclo."""
        self.is_running = False
        self.logger.info(f"[{self.worker_id}] Stop sinalizado.")
