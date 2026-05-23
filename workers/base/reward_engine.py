from __future__ import annotations
from dataclasses import dataclass
# pyrefly: ignore [missing-import]
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
        
        # Recupera o XP/Score acumulado anterior do worker
        recent = await self.memory.get_recent(result.worker_id, n=1)
        last_score = recent[0].score if recent else 50.0 # Começa no nível neutro (50)
        
        # Calcula a variação (XP ganho ou perdido no ciclo)
        delta = self.calculate_xp_delta(result)
        
        # Sistema com limite de 100: recompensas acumulam mas não viram números inatingíveis
        new_score = round(max(0.0, min(last_score + delta, 100.0)), 2)
        
        tier = self.resolve_tier(new_score, result)
        badges = self.resolve_badges(result, new_score)

        await self.memory.save_reward(
            worker_id=result.worker_id,
            cycle=result.cycle,
            score=new_score,
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
                "xp_delta": delta,
                **(result.metadata or {}),
            },
        )

        return RewardSummary(
            worker_id=result.worker_id,
            cycle=result.cycle,
            score=new_score,
            tier=tier,
            badges=badges,
        )

    def calculate_xp_delta(self, result: CycleResult) -> float:
        """Calcula a variação de pontos (XP) ganhos ou perdidos neste ciclo."""
        if result.simulated:
            return 0.0
        if not result.target:
            return 0.0 # Idle: não ganha nem perde
        if result.error or not result.db_success:
            return -15.0 # Falha crítica de sistema ou DB
            
        xp_delta = 0.0
        
        # Recompensas por produtividade (limitadas por ciclo para evitar farming)
        if result.extracted > 0:
            xp_delta += min(result.extracted * 0.5, 5.0)
        if result.inserted > 0:
            xp_delta += min(result.inserted * 1.0, 10.0)
        if result.classifier_success and result.classified > 0:
            xp_delta += min(result.classified * 1.0, 10.0)
            
        # Penalidade por erros na coleta/inserção
        if result.failed > 0:
            xp_delta -= min(result.failed * 2.0, 20.0)
            
        # Bônus de perfeição
        if result.success_rate >= 95 and result.failed == 0 and result.inserted > 0:
            xp_delta += 5.0
            
        return round(xp_delta, 2)

    def resolve_tier(self, score: float, result: CycleResult) -> str:
        if score >= 70: return "gold"
        if score >= 50: return "silver"
        return "bronze"

    def resolve_badges(self, result: CycleResult, score: float) -> list[str]:
        badges = []
        if not result.is_real_collection: return badges
        if result.failed == 0 and result.inserted > 0: badges.append("🎯 Persistência OK")
        if result.classifier_success and result.classified >= result.inserted and result.inserted > 0: badges.append("🧠 IA OK")
        if score >= 85: badges.append("🏆 Alta performance")
        if result.duplicated > 0 and result.inserted > 0: badges.append("🔁 Upsert saudável")
        return badges
