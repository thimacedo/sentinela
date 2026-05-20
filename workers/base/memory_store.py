# workers/base/memory_store.py
"""
MemoryStore — persistência de métricas e rewards no Supabase.

Responsabilidades:
  - Salvar WorkerMetrics após cada ciclo
  - Salvar RewardResult após cada avaliação
  - Recuperar histórico recente por worker
  - Prover singleton do client Supabase

Não contém lógica de negócio — apenas I/O.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

from supabase import create_client, Client

if TYPE_CHECKING:
    from workers.base.worker_base import WorkerMetrics
    from workers.base.reward_engine import RewardResult


# ── Singleton Supabase ────────────────────────────────────────────────────────

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """
    Retorna instância única do client Supabase.
    Lê credenciais do ambiente — nunca hardcoded.
    """
    global _supabase_client

    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            raise EnvironmentError(
                "SUPABASE_URL e SUPABASE_KEY devem estar definidos no ambiente."
            )

        _supabase_client = create_client(url, key)

    return _supabase_client


# ── MemoryStore ───────────────────────────────────────────────────────────────

class MemoryStore:
    """
    Camada de acesso a dados para o ecossistema de workers.

    Tabelas gerenciadas:
      - worker_metrics     → performance por ciclo
      - worker_rewards     → score e tier por ciclo
      - worker_suggestions → sugestões da IA pendentes de revisão
    """

    def __init__(self):
        self.db = get_supabase()

    # ── Métricas ──────────────────────────────────────────────────────────────

    async def save_metrics(self, metrics: WorkerMetrics) -> None:
        """Persiste métricas de um ciclo."""
        payload = {
            "worker_id":         metrics.worker_id,
            "cycle":             metrics.cycle,
            "items_collected":   metrics.items_collected,
            "items_failed":      metrics.items_failed,
            "duration_seconds":  round(metrics.duration_seconds, 3),
            "errors":            metrics.errors,
            "timestamp":         metrics.timestamp.isoformat(),
        }

        result = self.db.table("worker_metrics").insert(payload).execute()
        self._raise_if_error(result, "save_metrics")

    # ── Rewards ───────────────────────────────────────────────────────────────

    async def save(self, reward: RewardResult) -> None:
        """Persiste resultado de avaliação do RewardEngine."""
        payload = {
            "worker_id":      reward.worker_id,
            "cycle":          reward.cycle,
            "score":          round(reward.score, 2),
            "delta":          round(reward.delta, 2),
            "tier":           reward.tier,
            "badges":         reward.badges,
            "recommendation": reward.recommendation,
            "timestamp":      datetime.utcnow().isoformat(),
        }

        result = self.db.table("worker_rewards").insert(payload).execute()
        self._raise_if_error(result, "save_reward")

    async def get_recent(self, worker_id: str, n: int = 10) -> list[_RewardSnapshot]:
        """
        Retorna os últimos N rewards de um worker.
        """
        result = (
            self.db.table("worker_rewards")
            .select("*")
            .eq("worker_id", worker_id)
            .order("timestamp", desc=True)
            .limit(n)
            .execute()
        )

        self._raise_if_error(result, "get_recent")
        return [_RewardSnapshot(**row) for row in (result.data or [])]

    # ── Sugestões da IA ───────────────────────────────────────────────────────

    async def save_suggestion(
        self,
        worker_id: str,
        cycle: int,
        suggestion: str,
    ) -> None:
        """Persiste sugestão do AIAdvisor para revisão humana."""
        payload = {
            "worker_id":  worker_id,
            "cycle":      cycle,
            "suggestion": suggestion,
            "status":     "pending_review",
            "timestamp":  datetime.utcnow().isoformat(),
        }

        result = self.db.table("worker_suggestions").insert(payload).execute()
        self._raise_if_error(result, "save_suggestion")

    async def get_pending_suggestions(self) -> list[dict]:
        """Lista sugestões aguardando revisão humana."""
        result = (
            self.db.table("worker_suggestions")
            .select("id, worker_id, cycle, suggestion, timestamp")
            .eq("status", "pending_review")
            .order("timestamp", desc=True)
            .execute()
        )

        self._raise_if_error(result, "get_pending_suggestions")
        return result.data or []

    async def update_suggestion_status(
        self,
        suggestion_id: str,
        status: str,
    ) -> None:
        """Atualiza status de uma sugestão após revisão humana."""
        if status not in ("approved", "rejected"):
            raise ValueError(f"Status inválido: {status}. Use 'approved' ou 'rejected'.")

        result = (
            self.db.table("worker_suggestions")
            .update({"status": status})
            .eq("id", suggestion_id)
            .execute()
        )

        self._raise_if_error(result, "update_suggestion_status")

    # ── Utilitários ───────────────────────────────────────────────────────────

    def _raise_if_error(self, result, operation: str) -> None:
        if hasattr(result, "error") and result.error:
            raise RuntimeError(
                f"[MemoryStore.{operation}] Supabase error: {result.error}"
            )


class _RewardSnapshot:
    __slots__ = ("worker_id", "cycle", "score", "delta", "tier", "badges", "recommendation")

    def __init__(self, **kwargs):
        for key in self.__slots__:
            setattr(self, key, kwargs.get(key))
