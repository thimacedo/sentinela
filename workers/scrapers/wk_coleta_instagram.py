from __future__ import annotations

import logging
import asyncio
import os
import time
from typing import List, Dict, Any
from datetime import datetime, timezone

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service, clean_null_chars
from core.instagram_scraper_v2 import InstagramScraperV2

from core.local_buffer import local_buffer
from core.lexical_filter import lexical_filter
from core.process_cleaner import cleanup_orphans
from core.checkpoint_manager import CheckpointManager
from core.event_bus import local_bus
from core.circuit_breaker import scraper_circuit_breaker

logger = logging.getLogger("worker.ig_v2")

class WkColetaInstagram(BaseWorker):
    """
    Worker Instagram V2 (Independente).
    Implementa o fluxo completo de coleta e classificação usando o motor V2.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.consecutive_blocks = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self.scraper = InstagramScraperV2(
            headless=config.get("headless", True),
            max_retries=config.get("max_retries", 3),
            shutdown_event=getattr(self, "shutdown_event", None)
        )
        self.last_activity = time.time()  # v97.0: Heartbeat Watchdog

        # 🤖 Instancia o adaptador do ScrapeAgent
        from core.agent_scraper.worker_adapter import ScrapeAgentAdapter
        from core.ai_service import ai_service
        self.agent_adapter = ScrapeAgentAdapter(
            scraper=self.scraper,
            ai_service=ai_service,
            config=config,
        )

    def describe(self) -> str:
        return "Instagram Scraper V2 - Independente com Playwright"

    async def setup(self) -> None:
        self.scraper.shutdown_event = getattr(self, "shutdown_event", None)
        logger.info(f"🚀 Worker {self.worker_id} configurado.")
        try:
            cleanup_orphans()
        except Exception as e:
            logger.warning(f"⚠️ [V2] Falha ao limpar órfãos no setup: {e}")
        await local_buffer.sync_with_supabase(self.db)

    async def teardown(self) -> None:
        logger.info(f"🛑 Worker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        # v97.0: Heartbeat Watchdog - Detecta se o worker está preso em inatividade
        if time.time() - self.last_activity > 600:
            self.logger.warning("🚨 [Heartbeat] Scraper inativo por > 10min. Forçando reset do lock e rotação.")
            self.last_activity = time.time()
            if hasattr(self, 'current_target') and self.current_target:
                 await self.queue.rotate_target(self.current_target)

        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        # 🛡️ CIRCUIT BREAKER
        if not scraper_circuit_breaker.can_execute("instagram"):
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="circuit_breaker", simulated=False, error="circuit_open")
        
        current_cycle_config = dict(self.config)
        
        # 🛡️ HIBERNAÇÃO INTELIGENTE
        if self.consecutive_blocks >= 3:
            self.logger.warning(f"🛡️ [V2] {self.consecutive_blocks} bloqueios consecutivos. Hibernando por 1h para segurança...")
            await asyncio.sleep(3600)
            self.consecutive_blocks = 0

        # 🌙 MODO NOTURNO
        current_hour = datetime.now().hour
        if current_hour >= 23 or current_hour < 5:
            self.logger.info(f"🌙 [V2] Modo noturno ativo (Hora: {current_hour}h). Aguardando 300s (5min) para proteção do pool...")
            await asyncio.sleep(300)

        # 📦 SINCRONIZAÇÃO DE BACKGROUND
        if self.cycle % 5 == 0:
            await local_buffer.sync_with_supabase(self.db)

        self.seen_targets.clear()
        self.seen_queue_ids.clear()
        
        target = await self.queue.claim_next_target(
            current_cycle_config, self.seen_queue_ids, self.seen_targets,
            active_targets=getattr(self, 'active_targets', None),
        )

        if not target:
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="no_target", simulated=False, error="no_tasks_available")

        self.last_activity = time.time()
        self.current_target = target
        self.logger.info(f"🔄 [V2] Ciclo {self.cycle} | Alvo: @{target.username}")
        
        # 🧠 INTEGRAÇÃO DE INTELIGÊNCIA (v84.15): Pesquisa antes de coletar se for novo
        try:
            cand_check = self.db.table("candidatos").select("identidade_validada, cargo").eq("username", target.username).single().execute()
            if cand_check.data and (cand_check.data.get("identidade_validada") is None or cand_check.data.get("cargo") == "ANALISE_SOLICITADA"):
                from core.intelligence_service import intelligence_service
                self.logger.info(f"🔎 [V2] Alvo novo/não validado. Acionando inteligência para @{target.username}...")
                research_res = await intelligence_service.research_and_validate(target.username)
                
                if research_res and research_res.get("status_monitoramento") == "DESATIVADO":
                    self.logger.warning(f"🚫 [V2] Alvo @{target.username} desativado pela governança: {research_res.get('motivo_desativacao')}")
                    result = CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, error="purged_by_governance"
                    )
                    return result
        except Exception as e_intel:
            self.logger.warning(f"⚠️ [V2] Falha na integração de inteligência: {e_intel}")

        # Jitter inicial (PASA v52.0) para quebrar padrões
        import random
        jitter = random.uniform(5, 30)
        self.logger.debug(f"[V2] Aplicando jitter inicial de {jitter:.1f}s")
        await asyncio.sleep(jitter)

        await self.queue.mark_candidate_scraped(target)

        # 💥 CHECKPOINT INTRA-CYCLE (PASA v88.0 - Fase 8.5)
        checkpoint = CheckpointManager(
            db_client=self.db,
            worker_id=self.worker_id,
            candidato_id=target.username,
        )
        previous_cp = await checkpoint.load()
        resume_from_shortcode = previous_cp.get('last_shortcode') if previous_cp else None
        if resume_from_shortcode:
            self.logger.info(
                "🔄 [V2] Retomando ciclo de @%s a partir do post %s (checkpoint encontrado).",
                target.username, resume_from_shortcode,
            )

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0
        
        async def handle_post_scraped(shortcode: str, post_comments: List[Dict[str, Any]]):
            nonlocal inserted_total, duplicated_total, comments_count
            if not post_comments:
                return
            comments_count += len(post_comments)

            # ♻️ FILTRO LÉXICO (Pre-AI) - PASA v65.0
            filtered_comments = lexical_filter.filter_list(post_comments)
            
            # 🤖 DETECÇÃO DE COMPORTAMENTO COORDENADO (v71.0)
            from core.behavior_engine import behavior_engine
            filtered_comments = await behavior_engine.detect_coordinated_clusters(filtered_comments)

            if not filtered_comments:
                duplicated_total += len(post_comments)
                return

            safe_comments = []
            now = datetime.now(timezone.utc).isoformat()
            for c in filtered_comments:
                safe_c = {
                    "id_externo": c.get("id_externo"),
                    "texto_bruto": c.get("texto_bruto") or c.get("texto", ""),
                    "autor_username": c.get("autor_username"),
                    "data_publicacao": c.get("data_publicacao") or now,
                    "data_coleta": c.get("data_coleta") or now,
                    "candidato_id": c.get("candidato_id") or target.username,
                    "post_shortcode": c.get("post_shortcode") or shortcode,
                    "plataforma": c.get("plataforma") or "INSTAGRAM",
                    "tier_used": c.get("tier_used", 2),
                    "is_hate": False,   # Valor padrão
                }
                if c.get("is_bot"):
                    pericial_obs = f"[BOT DETECTED] Padrão: {c.get('bot_pattern')}"
                    safe_c["analise_pericial"] = pericial_obs
                    safe_c["categoria_ia"] = "CAMPANHA_COORDENADA"
                safe_comments.append(safe_c)

            # --- BUFFER DE EMERGÊNCIA SQLITE (Zero Loss Policy v65.0) ---
            local_buffer.save(safe_comments)

            inserted = 0
            try:
                # 🛡️ TENTATIVA 1: Upsert Completo (v63.0)
                res = self.db.table("comentarios").upsert(
                    clean_null_chars(safe_comments), 
                    on_conflict="id_externo",
                    ignore_duplicates=True
                ).execute()
                
                inserted = len(res.data) if res.data else 0
                inserted_total += inserted
                duplicated_total += len(post_comments) - inserted
            except Exception as e_upsert:
                self.logger.warning(f"⚠️ [V2] Erro de Schema no post {shortcode}: {e_upsert}. Iniciando Fallback...")
                
                emergency_comments = []
                for sc in safe_comments:
                    emergency_comments.append({
                        "id_externo": sc["id_externo"],
                        "texto_bruto": sc["texto_bruto"],
                        "candidato_id": sc["candidato_id"],
                        "post_shortcode": sc["post_shortcode"],
                        "autor_username": sc["autor_username"],
                        "data_publicacao": sc["data_publicacao"],
                        "data_coleta": sc["data_coleta"],
                        "plataforma": sc["plataforma"],
                        "tier_used": sc["tier_used"]
                    })

                try:
                    res = self.db.table("comentarios").upsert(
                        clean_null_chars(emergency_comments),
                        on_conflict="id_externo",
                        ignore_duplicates=True
                    ).execute()
                    
                    if res.data:
                        inserted = len(res.data)
                        inserted_total += inserted
                        duplicated_total += len(post_comments) - inserted
                except Exception as e2:
                    self.logger.error(f"❌ [V2] Falha total na persistência incremental do post {shortcode}: {e2}")

            # --- SINALIZAÇÃO DE NOVO DADO (Pipeline Reativo Fase 9) ---
            if inserted > 0:
                self.logger.info(f"⚡ [EventBus] Sinalizando AIProcessorWorker: {inserted} novos registros.")
                local_bus.signal_new_data()

            # 💥 SALVAMENTO DE CHECKPOINT POR POST (Fase 8.5)
            posts_done = previous_cp.get('posts_done', 0) + 1 if previous_cp else 1
            await checkpoint.save(
                last_shortcode=shortcode,
                posts_done=posts_done,
                comments_done=inserted_total,
            )
            self.logger.info(f"💥 [V2] Checkpoint intermediário salvo para post {shortcode} (+{inserted} novos comentários).")

        try:
            # 1. Scraping com o Loop Cognitivo do ScrapeAgent (OODA)
            self.logger.info(f"🤖 [ScrapeAgent] Iniciando ciclo cognitivo OODA para @{target.username}...")
            agent_result = await self.agent_adapter.run_scrape_cycle(
                username=target.username,
                max_posts=current_cycle_config.get('max_posts', 3),
                max_comments_per_post=100,
                candidato_id=target.candidato_id,
                resume_after_shortcode=resume_from_shortcode,
                on_post_scraped=handle_post_scraped,
            )
            
            if not agent_result.success and agent_result.error:
                if getattr(agent_result, 'is_control_signal', False) or agent_result.error == "healer_restart_requested":
                    self.logger.info(f"🔄 [Worker] Ciclo de healing concluído para @{target.username}. Retomando sem penalidade.")
                    result = CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, simulated=False, 
                        error="healer_restart", db_success=False
                    )
                    result.is_control_signal = True
                    return result
                raise RuntimeError(agent_result.error)
            
            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("instagram")
            target.post_metas = []

        except Exception as e:
            self.consecutive_blocks += 1
            error_str = str(e).lower()
            status_code = None
            if "429" in error_str: status_code = 429
            elif "403" in error_str: status_code = 403
            elif "404" in error_str: status_code = 404
            
            scraper_circuit_breaker.record_failure("instagram", status_code=status_code, error_msg=str(e))

            if isinstance(e, ValueError) and "invalid_target" in str(e):
                self.logger.error(f"🚫 [V2] Alvo @{target.username} marcado como INVÁLIDO (404/Privado/Mismatch).")
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, 
                    error=str(e), db_success=False
                )
                return result
                
            if "all_sessions_blocked" in str(e):
                self.logger.error(f"🛑 [V2] TODAS AS SESSÕES EM COOLDOWN OU EXPIRADAS!")
                self.logger.error(f"👉 Se todas as sessões expiraram, execute o comando abaixo no terminal para renová-las de forma interativa:")
                self.logger.error(f"   python scripts/export_playwright_cookies.py --force --interactive")
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, 
                    error="all_sessions_blocked", db_success=False
                )
                return result
                
            self.logger.error(f"⚠️ [V2] Erro inesperado na extração de @{target.username}: {e}")
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="v2_engine", extracted=0, simulated=False, 
                error=str(e), db_success=False
            )
            return result

        try:
            stats = self.scraper.stats

            if comments_count == 0:
                error_reason = "no_comments_found"
                if stats.get("junk_detected", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Apenas lixo detectado para @{target.username}. Sinalizando falha de extração.")
                    error_reason = "junk_detected"
                elif stats.get("posts_found", 0) == 0:
                    self.logger.warning(f"⚠️ [V2] Nenhum post encontrado na página do perfil @{target.username}.")
                    error_reason = "no_posts_found"
                elif stats.get("errors", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Erros de Playwright/Extração detectados ({stats.get('errors')} erros) durante a raspagem de @{target.username}.")
                    error_reason = "playwright_error"
                elif stats.get("posts_scraped", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Posts abertos com sucesso, mas nenhum comentário encontrado para @{target.username}.")
                    error_reason = "no_comments_in_posts"
                
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, error=error_reason
                )
                return result

            final_extracted = comments_count
            
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="v2_engine",
                extracted=final_extracted,
                inserted=inserted_total,
                duplicated=duplicated_total,
                db_success=inserted_total > 0,
                simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )

            await checkpoint.clear()
            return result

        except Exception as e:
            self.logger.error(f"💥 Erro crítico no ciclo V2: {e}")
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )
            return result
        finally:
            if isinstance(result, dict) and result.get("error"):
                target.error = result.get("error")
            elif hasattr(result, "error") and result.error:
                target.error = result.error

            if target and getattr(target, 'source', '') == 'fila_coleta_atomic' and target.queue_id:
                await self.queue.update_target_metrics(target)
                
                final_status = "CONCLUIDO"
                if hasattr(result, 'error') and result.error:
                    err = result.error
                    if err in ('junk_detected', 'invalid_target: 404_not_found'):
                        final_status = 'SEM_DADOS_RECENTES'
                    elif err in ('all_sessions_blocked', 'shutdown_requested', 'healer_restart'):
                        final_status = 'PENDENTE'
                    else:
                        final_status = 'FALHA'
                        # Registra na Dead Letter Queue (DLQ) para resiliência (v100.0)
                        try:
                            from core.skills.dead_letter_queue import dead_letter_queue
                            await dead_letter_queue.add_failed_target(
                                target_username=target.username,
                                error_type="extraction_failure",
                                error_message=str(err),
                                stack_trace=getattr(result, "stack_trace", "") or "Falha de extracao no InstagramScraperV2",
                                original_target_id=getattr(target, "candidato_id", None),
                                queue_id=target.queue_id,
                                platform="INSTAGRAM"
                            )
                        except Exception as e_dlq:
                            logger.warning("[V2] Falha ao enviar alvo para a DLQ: %s", e_dlq)
                try:
                    await self.queue.release_atomic(target.queue_id, final_status, self.worker_id)
                except Exception as e_rel:
                    logger.warning("[V2] Falha no release atômico: %s", e_rel)
            else:
                await self.queue.rotate_target(target)
