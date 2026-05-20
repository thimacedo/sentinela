from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workers.base.worker_base import WorkerMetrics
    from workers.base.memory_store import MemoryStore


@dataclass
class RewardResult:
    worker_id: str
    cycle: int
    score: float
    delta: float
    tier: str
    badges: list[str]
    recommendation: str


class RewardEngine:
    TIER_THRESHOLDS = {"elite": 90, "gold": 70, "silver": 50, "bronze": 0}
    TIER_INTERVAL   = {"elite": 60, "gold": 180, "silver": 300, "bronze": 600}

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store

    async def evaluate(self, worker, metrics: WorkerMetrics) -> RewardResult:
        score   = self._calculate_score(metrics)
        history = await self.memory.get_recent(worker.worker_id, n=10)
        delta   = score - (history[0].score if history else score)
        tier    = self._get_tier(score)
        badges  = self._award_badges(metrics, score, history)

        result = RewardResult(
            worker_id=worker.worker_id,
            cycle=metrics.cycle,
            score=score,
            delta=delta,
            tier=tier,
            badges=badges,
            recommendation=self._recommend(score, delta, metrics),
        )

        await self.memory.save(result)
        return result

    def _calculate_score(self, metrics: WorkerMetrics) -> float:
        total = metrics.items_collected + metrics.items_failed
        if total == 0:
            return 0.0

        success_score = metrics.success_rate * 50
        volume_score  = min(metrics.items_collected / 100, 1.0) * 30
        speed_score   = max(0, 20 - metrics.duration_seconds / 60)
        error_penalty = len(metrics.errors) * 5

        return max(0.0, min(100.0, success_score + volume_score + speed_score - error_penalty))

    def _get_tier(self, score: float) -> str:
        for tier, threshold in self.TIER_THRESHOLDS.items():
            if score >= threshold:
                return tier
        return "bronze"

    def _award_badges(self, metrics, score: float, history: list) -> list[str]:
        badges = []
        if metrics.success_rate == 1.0:
            badges.append("🎯 Perfect Run")
        if score >= 90:
            badges.append("⚡ Elite Performance")
        if len(history) >= 5 and all(h.score > 70 for h in history[:5]):
            badges.append("🔥 5-Cycle Streak")
        if metrics.items_collected > 500:
            badges.append("📦 High Volume")
        return badges

    def _recommend(self, score: float, delta: float, metrics) -> str:
        if score < 30:
            return "CRÍTICO: Solicitar análise de IA imediatamente"
        if score < 50 and delta < 0:
            return "Degradação contínua — verificar mudanças na API alvo"
        if score > 80 and delta > 5:
            return "Performance excelente — considerar aumentar volume"
        return "Operação normal"

    def get_interval(self, tier: str) -> int:
        return self.TIER_INTERVAL.get(tier, 300)
