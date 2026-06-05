from __future__ import annotations
import asyncio
import logging
import time
import gc
import ctypes
import platform
from typing import List, Any
from workers.base.worker_base import BaseWorker, WorkerMetrics
from workers.base.reward_engine import RewardEngine, RewardSummary
from workers.base.memory_store import MemoryStore
from workers.ai.ai_advisor import AIAdvisor
from workers.base.cycle_result import CycleResult

logger = logging.getLogger("orchestrator")


class SentinelaOrchestrator:
    def __init__(self, reward_engine: RewardEngine, ai_advisor: AIAdvisor):
        self.reward_engine  = reward_engine
        self.ai_advisor     = ai_advisor
        self.logger         = logging.getLogger("orchestrator")
        self._workers: List[BaseWorker] = []
        self._active_targets: set = set()
        self._target_timestamps: dict[str, float] = {} # PASA v57.0: Monitor de Alvos
        self._claim_lock = asyncio.Lock()
        self._banned_until: dict[str, float] = {}
        self._cycle_total = 0

    def _perform_self_healing(self):
        """Ações de autocura de infraestrutura (v57.1)."""
        # 1. Limpeza de Memória (Preventiva contra OOM)
        gc.collect()
        
        # 2. Flush de Memória (Nível SO - Apenas Linux/Render)
        if platform.system() == "Linux":
            try:
                libc = ctypes.CDLL("libc.so.6")
                libc.malloc_trim(0)
                logger.debug("[orchestrator] 🧊 Flush de memória (malloc_trim) concluído.")
            except Exception as e:
                logger.warning("[orchestrator] Falha ao executar malloc_trim: %s", e)

        # 3. Limpeza de Navegadores Órfãos (PASA v65.1)
        try:
            from core.process_cleaner import cleanup_orphans
            cleanup_orphans()
        except Exception as e:
            logger.warning("[orchestrator] Falha ao executar cleanup_orphans na autocura: %s", e)

    def register(self, worker: BaseWorker) -> None:
        self._workers.append(worker)
        logger.info("[orchestrator] registrado: %s", worker.worker_id)
        
        # 2. Resgate de Alvos (Zombie Cleanup)
        # Se um alvo está 'ativo' há mais de 20 minutos, provavelmente o worker travou
        now = time.time()
        stale_targets = [t for t, ts in self._target_timestamps.items() if (now - ts) > 1200]
        for t in stale_targets:
            logger.warning("[orchestrator] 🧟 Resgatando alvo zumbi: @%s", t)
            if t in self._active_targets:
                self._active_targets.remove(t)
            if t in self._target_timestamps:
                del self._target_timestamps[t]

    async def run_cycle_with_validation_v2(self, worker: BaseWorker):
        """Versão principal que executa o ciclo do worker, avalia recompensas, 
        persiste métricas, aciona o AIAdvisor se necessário e gerencia suspensões.
        Retorna um CycleContext contendo o CycleResult e o RewardSummary."""
        self._cycle_total += 1
        if self._cycle_total % 10 == 0:
            self._perform_self_healing()

        # 1. Gestão de Suspensão por Reputação Zero
        if worker.worker_id in self._banned_until:
            if time.time() < self._banned_until[worker.worker_id]:
                logger.debug("[%s] ⏳ Cumprindo suspensão (improdutividade). Ignorando ciclo.", worker.worker_id)
                result = CycleResult(
                    worker_id=worker.worker_id,
                    cycle=getattr(worker, "cycle", 0),
                    simulated=True,
                    error="worker_suspended"
                )
                reward = RewardSummary(
                    worker_id=worker.worker_id,
                    cycle=result.cycle,
                    score=0.0,
                    tier="critical",
                    badges=[]
                )
                from dataclasses import dataclass
                @dataclass
                class CycleContext:
                    cycle_result: CycleResult
                    reward: Any
                return CycleContext(cycle_result=result, reward=reward)
            else:
                del self._banned_until[worker.worker_id]
                logger.info("[%s] 🔄 Suspensão encerrada. Worker reintegrado ao pool.", worker.worker_id)

        # 2. Preparação do Worker
        worker.active_targets = self._active_targets
        worker.claim_lock = self._claim_lock
        worker.shutdown_event = getattr(self, "shutdown_event", None)

        # 3. Execução do Ciclo
        result = await worker.run_cycle()

        if not isinstance(result, CycleResult):
            logger.warning(
                "[orchestrator] %s retornou resultado inválido. Marcando como simulado.",
                worker.worker_id,
            )
            result = CycleResult(
                worker_id=worker.worker_id,
                cycle=getattr(worker, "cycle", 0),
                simulated=True,
                error="worker_returned_invalid_result",
            )

        # 4. Avaliação de Recompensas
        reward = await self.reward_engine.process_result(result)

        # 5. Persistência de Métricas (v70.2)
        try:
            from datetime import datetime, timezone
            await self.reward_engine.memory.save_metrics(WorkerMetrics(
                worker_id=result.worker_id,
                cycle=result.cycle,
                items_collected=result.extracted,
                items_failed=result.failed,
                duration_seconds=result.duration,
                errors=[result.error] if result.error else [],
                timestamp=datetime.now(timezone.utc)
            ))
        except Exception as e:
            logger.warning("[orchestrator] Falha ao salvar métricas: %s", e)

        db_status = "n/a" if result.simulated else ("ok" if result.db_success else "falhou")
        ia_status = "n/a" if result.simulated else ("ok" if result.classifier_success else "nao")

        logger.info(
            "[%s] ciclo #%s | target=%s | origem=%s | extraidos=%s | inseridos=%s | "
            "duplicados=%s | classificados=%s | falhas=%s | db=%s | ia=%s | "
            "score=%.1f | tier=%s | simulado=%s | erro=%s",
            result.worker_id, result.cycle,
            result.target or "N/A", result.source or "N/A",
            result.extracted, result.inserted, result.duplicated,
            result.classified, result.failed,
            db_status, ia_status,
            reward.score, reward.tier,
            result.simulated, result.error or "nenhum",
        )

        if reward.xp_report:
            logger.info(
                "[%s] 📊 DETALHAMENTO DE RECOMPENSAS (Ciclo #%s):\n%s\n  - Reputação Consolidada: %.1f/100.0 (Tier: %s)",
                result.worker_id, result.cycle, reward.xp_report, reward.score, reward.tier
            )

        if reward.badges:
            logger.info("[%s] badges: %s", result.worker_id, reward.badges)

        # 6. Gatilho de Diagnóstico (PASA v56.3)
        # Se o ciclo for vazio (extracted=0) ou degradado, acionamos o Advisor para buscar melhoria no processo.
        is_empty = result.extracted == 0 and result.target is not None and result.error not in ["purged_by_governance", "no_tasks_available"]
        degraded = reward.score < 40 or reward.tier in ("critical", "db_failed")

        if not result.simulated and (degraded or is_empty):
            logger.info("[%s] 🧠 Acionando AIAdvisor para diagnóstico (motivo: %s)",
                        result.worker_id, "vazio" if is_empty else "degradado")
            await self.ai_advisor.analyze_and_suggest(worker, result)
        elif not result.simulated:
            logger.debug("[%s] AIAdvisor ignorado (tier=%s score=%.1f)", result.worker_id, reward.tier, reward.score)

        # --- ATIVACAO REATIVA DE SUBAGENTES ANALITICOS (PASA v88.1) ---
        if not result.simulated and "ai-processor" in result.worker_id and result.classifier_success and result.classified > 0:
            logger.info("[%s] Disparando subagentes analiticos (NetworkMinerAgent & TreasurerAgent) em background...", result.worker_id)
            
            async def _run_subagents_async():
                try:
                    from workers.analytics.network_agent import NetworkMinerAgent
                    from workers.financial.treasurer_agent import TreasurerAgent
                    
                    net_agent = NetworkMinerAgent()
                    treas_agent = TreasurerAgent()
                    
                    await asyncio.gather(
                        net_agent.run_analysis(),
                        treas_agent.run_financial_audit(),
                        return_exceptions=True
                    )
                except Exception as sa_err:
                    logger.warning("[orchestrator] Erro ao executar subagentes analiticos em background: %s", sa_err)
            
            asyncio.create_task(_run_subagents_async())

        # 7. Suspensão se reputação cair a zero
        if not result.simulated:
            delta_xp = getattr(result, "metadata", {}).get("xp_delta", 0.0) if getattr(result, "metadata", None) else 0.0
            if reward.score <= 0.0 and delta_xp < 0.0:
                logger.error("[%s] 🛑 REPUTAÇÃO ZERO. Aplicando suspensão disciplinar.", result.worker_id)
                self._banned_until[result.worker_id] = time.time() + 1800

        from dataclasses import dataclass
        @dataclass
        class CycleContext:
            cycle_result: CycleResult
            reward: Any

        return CycleContext(cycle_result=result, reward=reward)

    async def run_cycle_with_validation(self, worker: BaseWorker) -> float:
        """Legado para compatibilidade se outros scripts chamarem. Retorna o intervalo recomendado em segundos."""
        ctx = await self.run_cycle_with_validation_v2(worker)
        return float(self.reward_engine.get_interval(ctx.reward.tier))

    async def run_all(self) -> None:
        # 🧹 Faxina de processos órfãos de navegadores antes de iniciar o loop
        try:
            from core.process_cleaner import cleanup_orphans
            cleanup_orphans()
        except Exception as e:
            logger.warning("[orchestrator] Falha na limpeza de órfãos no run_all: %s", e)

        if not self._workers:
            logger.warning("[orchestrator] Nenhum worker registrado.")
            return
        
        logger.info("[orchestrator] Iniciando %s worker(s) em loops individuais...", len(self._workers))
        
        async def _worker_loop(worker: BaseWorker):
            while True:
                if getattr(self, "shutdown_event", None) and self.shutdown_event.is_set():
                    logger.info("[%s] Shutdown detectado. Saindo do loop.", worker.worker_id)
                    break
                result = await self.run_cycle_with_validation_v2(worker)
                
                # --- SMART WAIT (PASA v85.12 & Pipeline Reativo Fase 9) ---
                if result.cycle_result.error == "no_tasks_available":
                    if "ai-processor" in worker.worker_id.lower():
                        from core.event_bus import local_bus
                        idle_wait = 1200.0
                        logger.info("[%s] 💤 Fila vazia. Aguardando novo sinal via EventBus (Pipeline Reativo)...", worker.worker_id)
                        # Aguarda o sinal de novos dados do Scraper (ou timeout)
                        acordado_por_sinal = await local_bus.wait_for_data(timeout=idle_wait)
                        if acordado_por_sinal:
                            logger.info("[%s] ⚡ Sinal recebido! Reativando AIProcessor imediatamente.", worker.worker_id)
                            local_bus.clear_signal()
                    else:
                        idle_wait = 1200.0 # 20 minutos de sono profundo
                        logger.info("[%s] 💤 Fila vazia. Entrando em modo de espera (%.0fs).", worker.worker_id, idle_wait)
                        await asyncio.sleep(idle_wait)
                elif result.cycle_result.error == "worker_suspended":
                    logger.info("[%s] ⏳ Worker suspenso. Aguardando 60s antes de nova verificação.", worker.worker_id)
                    await asyncio.sleep(60.0)
                else:
                    # Se foi produtivo, aplica cooldown normal, mas o AIProcessor pode pular o cooldown se tiver sinal?
                    # Não, mantemos o cooldown para evitar rate-limit de APIs.
                    wait_time = float(self.reward_engine.get_interval(result.reward.tier))
                    logger.debug("[%s] Aguardando %.0fs de cooldown space.", worker.worker_id, wait_time)
                    await asyncio.sleep(wait_time)


        # Roda todos em paralelo, cada um com seu próprio ritmo de cooldown
        await asyncio.gather(*(_worker_loop(w) for w in self._workers))

    def stop_all(self) -> None:
        for w in self._workers:
            w.stop()
        logger.info("[orchestrator] Stop: %s worker(s).", len(self._workers))

    @property
    def worker_ids(self) -> List[str]:
        return [w.worker_id for w in self._workers]
