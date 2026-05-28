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
    xp_report: str = ""


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
        
        # Calcula a variação (XP ganho ou perdido no ciclo) e gera o relatório
        delta, report = self.generate_xp_report_and_delta(result)
        
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
            xp_report=report,
        )

    def calculate_xp_delta(self, result: CycleResult) -> float:
        """Calcula a variação de pontos (XP) ganhos ou perdidos neste ciclo."""
        delta, _ = self.generate_xp_report_and_delta(result)
        return delta

    def generate_xp_report_and_delta(self, result: CycleResult) -> tuple[float, str]:
        """Calcula o delta de XP e gera um relatório detalhado do ciclo."""
        if result.simulated:
            return 0.0, "  - Status: Ciclo simulado (Dry-Run)\n  - Delta: +0.0 XP"
        if not result.target and not (result.metadata and "xp_delta" in result.metadata):
            return 0.0, "  - Status: Sem alvo (Ocioso/Idle)\n  - Delta: +0.0 XP"
            
        # --- SUPORTE A XP MANUAL/METADATA (v84.9) ---
        # Se o worker já calculou seu XP (comum para workers de inteligência/pesquisa)
        if result.metadata and "xp_delta" in result.metadata:
            delta = float(result.metadata["xp_delta"])
            report = f"  - Inteligência: {result.source or 'worker'} finalizado\n"
            if "quality" in result.metadata:
                report += f"  - Qualidade: {result.metadata['quality']:.2f}/1.0\n"
            if result.error:
                report += f"  - Status: ⚠️ {result.error}\n"
            report += f"  - Delta do Ciclo: {delta:+.1f} XP"
            return delta, report

        # Erros legítimos de dados vazios não devem ser tratados como falha crítica de sistema.
        # Falha de banco só é crítica se havia dados extraídos para persistir.
        if result.error == "purged_by_governance":
            return 5.0, "  - Status: 🧹 Alvo expurgado pela governança\n  - Delta: +5.0 XP"
        if result.error == "no_tasks_available":
            return 0.0, "  - Status: ⏳ Sem tarefas no momento (Idle)\n  - Delta: +0.0 XP"

        is_system_error = result.error and result.error != "no_comments_found"
        is_db_failure = not result.db_success and result.extracted > 0
        
        if is_system_error or is_db_failure:
            motivo = result.error if is_system_error else "Falha na gravação do banco"
            return -15.0, f"  - Status: ❌ Falha Crítica ({motivo})\n  - Delta: -15.0 XP"
            
        lines = []
        delta = 0.0
        
        # 1. Coleta
        if result.extracted > 0:
            val = min(result.extracted * 0.5, 5.0)
            delta += val
            lines.append(f"  - Coleta ({result.source or 'scrapers'}): OK ({result.extracted} extraídos) -> +{val:.1f} XP")
        else:
            # PENALIZAÇÃO DE VACUIDADE (v56.2): 0 comentários extraídos é baixa performance
            delta -= 5.0
            lines.append(f"  - Coleta: ⚠️ Ineficiente (0 comentários encontrados) -> -5.0 XP")
            
        # 2. Banco
        if result.inserted > 0:
            val = min(result.inserted * 1.5, 15.0) # Aumentado peso da inserção real
            delta += val
            lines.append(f"  - Banco (Supabase): OK ({result.inserted} novos gravados) -> +{val:.1f} XP")
        elif result.extracted > 0:
            lines.append(f"  - Banco (Supabase): OK (0 novos gravados, todos duplicados) -> +0.0 XP")
            
        # 3. Classificação
        if result.classifier_success and result.classified > 0:
            val = min(result.classified * 1.0, 10.0)
            delta += val
            lines.append(f"  - IA (Classificação): OK ({result.classified} processados) -> +{val:.1f} XP")
            
        # 4. Falhas
        if result.failed > 0:
            val = min(result.failed * 2.0, 20.0)
            delta -= val
            lines.append(f"  - Falhas/Erros: ⚠️ {result.failed} falhas no ciclo -> -{val:.1f} XP")
            
        # 5. Bônus
        if result.success_rate >= 95 and result.failed == 0 and result.inserted > 0:
            delta += 5.0
            lines.append(f"  - Bônus Perfeição: Sucesso {result.success_rate:.1f}% -> +5.0 XP")
            
        report = "\n".join(lines) + f"\n  - Delta do Ciclo: {delta:+.1f} XP"
        return round(delta, 2), report

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
