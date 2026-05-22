from __future__ import annotations
from dataclasses import dataclass
from workers.base.cycle_result import CycleResult

# Intervalos em segundos por tier
_TIER_INTERVALS = {
    "gold":     120,
    "silver":   300,
    "bronze":   480,
    "critical": 600,
    "db_failed":600,
    "idle":     300,
    "dry_run":  300,
}

@dataclass
class RewardSummary:
    worker_id: str
    cycle: int
    score: float
    tier: str
    badges: list[str]


class RewardEngine:
    def __init__(self, memory):
        self.memory = memory

    def get_interval(self, tier: str) -> int:
        """Retorna intervalo em segundos para o proximo ciclo baseado no tier."""
        return _TIER_INTERVALS.get(tier, 300)

    async def process_result(self, result: CycleResult) -> RewardSummary:
        """Avalia e persiste o resultado do ciclo usando contrato CycleResult."""
        score = self.calculate_score(result)
        tier = self.resolve_tier(score, result)
        badges = self.resolve_badges(result, score)

        await self.memory.save_reward(
            worker_id=result.worker_id,
            cycle=result.cycle,
            score=score,
            tier=tier,
            collected=result.inserted,
            success_rate=result.success_rate,
            badges=badges,
            metadata={
                "cycle": result.cycle,
                "target": result.target,
                "target_id": result.target_id,
                "source": result.source,
                "extracted": result.extracted,
                "normalized": result.normalized,
                "inserted": result.inserted,
                "duplicated": result.duplicated,
                "classified": result.classified,
                "audit_checked": result.audit_checked,
                "failed": result.failed,
                "db_success": result.db_success,
                "classifier_success": result.classifier_success,
                "simulated": result.simulated,
                "error": result.error,
                **(result.metadata or {}),
            },
        )

        return RewardSummary(
            worker_id=result.worker_id,
            cycle=result.cycle,
            score=score,
            tier=tier,
            badges=badges,
        )

    def calculate_score(self, result: CycleResult) -> float:
        if result.simulated:
            return 0.0
        if not result.target:
            return 5.0
        if result.error or not result.db_success:
            return 10.0
        if result.extracted <= 0:
            return 15.0
        if result.inserted + result.duplicated <= 0:
            return 20.0

        score = 40.0
        score += min(result.extracted * 1.0, 15.0)
        score += min(result.inserted * 2.0, 25.0)
        if result.classifier_success and result.classified > 0:
            score += min(result.classified * 1.5, 15.0)
        score += min(result.duplicated * 0.3, 5.0)
        score -= min(result.failed * 5.0, 35.0)

        if result.success_rate >= 95 and result.failed == 0:
            score += 10.0

        return round(max(0.0, min(score, 100.0)), 2)

    def resolve_tier(self, score: float, result: CycleResult) -> str:
        if result.simulated: return "dry_run"
        if not result.target: return "idle"
        if not result.db_success: return "db_failed"
        if score >= 70: return "gold"
        if score >= 50: return "silver"
        if score >= 25: return "bronze"
        return "critical"

    def resolve_badges(self, result: CycleResult, score: float) -> list[str]:
        badges = []
        if not result.is_real_collection: return badges
        if result.failed == 0 and result.inserted > 0: badges.append("🎯 Persistência OK")
        if result.classifier_success and result.classified >= result.inserted and result.inserted > 0: badges.append("🧠 IA OK")
        if score >= 85: badges.append("🏆 Alta performance")
        if result.duplicated > 0 and result.inserted > 0: badges.append("🔁 Upsert saudável")
        return badges
