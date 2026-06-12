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
from workers.base.cycle_result import CycleResult

logger = logging.getLogger("orchestrator")


class SentinelaOrchestrator:
    # Regras determinísticas para diagnóstico sem LLM (PASA v51.0)
    _REGRAS_DIAGNOSTICO = {
        "session": ["session", "login", "cookie", "expired", "auth", "sessao", "sessão"],
        "dom_change": ["selector", "not found", "element", "dom", "seletor"],
        "rate_limit": ["429", "rate limit", "too many", "blocked", "bloqueado"],
        "network": ["timeout", "connection", "refused", "unreachable", "conexão"],
        "no_posts": ["no_posts_found"],
        "empty_posts": ["no_comments_in_posts"],
        "playwright_fault": ["playwright_error"],
        "junk_data": ["junk_detected"],
    }
    _SUGESTOES_PADRAO = {
        "session": "Sessão expirada detectada. SUGESTÃO: Verificar e renovar cookies do Instagram via script de export.",
        "dom_change": "Seletor DOM falhou. SUGESTÃO: Auditar seletores CSS no instagram_scraper_v2.py e atualizar.",
        "rate_limit": "Rate limit atingido. SUGESTÃO: Aumentar jitter entre requisições e reduzir MAX_POSTS_PER_PROFILE.",
        "network": "Falha de rede detectada. SUGESTÃO: Verificar conectividade e aguardar recuperação automática.",
        "no_posts": "Nenhum post foi localizado na página do perfil. SUGESTÃO: O perfil pode ser privado, não possuir publicações ou a página do Instagram falhou no carregamento inicial.",
        "empty_posts": "Os posts foram acessados com sucesso, mas não continham nenhum comentário. SUGESTÃO: O perfil do candidato está sem engajamento recente ou os comentários estão desativados.",
        "playwright_fault": "Erro de execução do navegador/Playwright. SUGESTÃO: Reiniciar processos zumbis do Chromium ou verificar integridade da instalação do driver.",
        "junk_data": "Apenas dados irrelevantes ou lixo de renderização detectados. SUGESTÃO: Verificar se a conta do Instagram caiu em checkpoint de segurança ou desafio CAPTCHA.",
        "unknown": "Erro desconhecido. SUGESTÃO: Verificar logs detalhados em logs/main_runner.json.",
    }

    def __init__(self, reward_engine: RewardEngine, ai_advisor=None):
        self.reward_engine  = reward_engine
        self.ai_advisor     = ai_advisor  # Mantido por compat. mas não usado
        self.memory         = MemoryStore()
        self.logger         = logging.getLogger("orchestrator")
        self._workers: List[BaseWorker] = []
        self._active_targets: set = set()
        self._target_timestamps: dict[str, float] = {}
        self._claim_lock = asyncio.Lock()
        self._banned_until: dict[str, float] = {}
        self._cycle_total = 0

    async def _perform_self_healing(self):
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

        # 4. Sincronização de Contexto Forense (PASA v51.0)
        # Recarrega o cache do CONTEXTO_CLASSIFICACAO.md a cada 100 ciclos
        if self._cycle_total % 100 == 0:
            try:
                from core.ai_service import ai_service
                ai_service.refresh_prompt_cache()
                logger.debug("[orchestrator] Cache de contexto forense recarregado.")
            except Exception as e:
                logger.warning("[orchestrator] Falha ao recarregar cache forense: %s", e)
                
        # 5. Pré-Aquecimento Frequente de Filas (v89.2)
        if self._cycle_total % 10 == 0:
            try:
                from core.queue_manager import QueueManager
                from core.db import db_client
                queue_manager = QueueManager(db_client.client)
                await queue_manager.pre_warm_queues()
            except Exception as e:
                logger.warning("[orchestrator] Falha ao pré-aquecer filas na autocura: %s", e)

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
            await self._perform_self_healing()

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

        # 6. Diagnóstico determinístico (PASA v51.0 — zero tokens)
        is_empty = result.extracted == 0 and result.target is not None and result.error not in ["purged_by_governance", "no_tasks_available"]
        degraded = reward.score < 40 or reward.tier in ("critical", "db_failed")

        if not result.simulated and (degraded or is_empty) and result.error:
            error_lower = (result.error or "").lower()
            tipo = "unknown"
            for t, palavras in self._REGRAS_DIAGNOSTICO.items():
                if any(p in error_lower for p in palavras):
                    tipo = t
                    break
            sugestao = self._SUGESTOES_PADRAO[tipo]
            logger.info("[%s] 💡 Diagnóstico determinístico: tipo=%s | %s", result.worker_id, tipo, sugestao)
            try:
                await self.memory.save_suggestion(
                    worker_id=result.worker_id,
                    cycle=result.cycle,
                    suggestion=sugestao
                )
            except Exception as e:
                logger.warning("[orchestrator] Falha ao salvar sugestão: %s", e)
        elif not result.simulated:
            logger.debug("[%s] Diagnóstico ignorado (tier=%s score=%.1f)", result.worker_id, reward.tier, reward.score)

        # --- ATIVACAO REATIVA DE SUBAGENTES ANALITICOS (PASA v88.1) ---
        if not result.simulated and "ai-processor" in result.worker_id and result.classifier_success and result.classified > 0:
            logger.info("[%s] Disparando subagentes analiticos (SaMineracaoRedes & SaAuditoriaFinanceira) em background...", result.worker_id)
            
            async def _run_subagents_async():
                try:
                    from workers.analytics.sa_mineracao_redes import SaMineracaoRedes
                    from workers.financial.sa_auditoria_financeira import SaAuditoriaFinanceira
                    
                    net_agent = SaMineracaoRedes()
                    treas_agent = SaAuditoriaFinanceira()
                    
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
        """Executa todos os workers registrados em seus próprios loops (v89.2)."""
        # 🧹 Faxina de processos órfãos de navegadores antes de iniciar o loop
        try:
            from core.process_cleaner import cleanup_orphans
            cleanup_orphans()
        except Exception as e:
            logger.warning("[orchestrator] Falha na limpeza de órfãos no run_all: %s", e)

        # 🔥 PRÉ-AQUECIMENTO DE FILAS (v89.2)
        # Garante alvos prontos e limpa locks órfãos ANTES de disparar os loops
        try:
            from core.queue_manager import QueueManager
            from core.db import db_client
            queue_manager = QueueManager(db_client.client)
            await queue_manager.pre_warm_queues()
        except Exception as e:
            logger.error(f"[orchestrator] Falha no pré-aquecimento das filas: {e}")

        if not self._workers:
            logger.warning("[orchestrator] Nenhum worker registrado.")
            return

        logger.info("[orchestrator] Iniciando %d worker(s) em loops individuais...", len(self._workers))

        async def _worker_loop(worker: BaseWorker):

            while True:
                if getattr(self, "shutdown_event", None) and self.shutdown_event.is_set():
                    logger.info("[%s] Shutdown detectado. Saindo do loop.", worker.worker_id)
                    break
                result = await self.run_cycle_with_validation_v2(worker)
                
                # --- SMART WAIT (PASA v85.12 & Pipeline Reativo Fase 9) ---
                if result.cycle_result.error == "no_tasks_available":
                    is_ai_processor = "ai-processor" in worker.worker_id.lower()
                    is_revisao_online = "sa-revisao-online" in worker.worker_id.lower()
                    
                    if is_ai_processor or is_revisao_online:
                        from core.event_bus import local_bus
                        idle_wait = 1200.0
                        logger.info("[%s] 💤 Fila vazia. Aguardando novo sinal via EventBus (Pipeline Reativo)...", worker.worker_id)
                        
                        if is_ai_processor:
                            acordado = await local_bus.wait_for_comments(timeout=idle_wait)
                            if acordado:
                                logger.info("[%s] ⚡ Novos comentários detectados! Reativando worker.", worker.worker_id)
                                local_bus.clear_comments_signal()
                        else: # is_revisao_online
                            acordado = await local_bus.wait_for_suspects(timeout=idle_wait)
                            if acordado:
                                logger.info("[%s] ⚡ Novos itens SUSPEITOS detectados! Reativando worker.", worker.worker_id)
                                local_bus.clear_suspects_signal()
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
