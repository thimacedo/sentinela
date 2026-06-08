from __future__ import annotations

import logging
import asyncio
import os
from typing import List, Dict

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

    def describe(self) -> str:
        return "Instagram Scraper V2 - Independente com Playwright"

    async def setup(self) -> None:
        logger.info(f"🚀 Worker {self.worker_id} configurado.")
        try:
            cleanup_orphans()
        except Exception as e:
            logger.warning(f"⚠️ [V2] Falha ao limpar órfãos no setup: {e}")
        await local_buffer.sync_with_supabase(self.db)

    async def teardown(self) -> None:
        logger.info(f"🛑 Worker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        # 🛡️ CIRCUIT BREAKER (PASA v94.3)
        if not scraper_circuit_breaker.can_execute("instagram"):
            self.logger.warning("🚫 [V2] Circuito ABERTO para Instagram. Pulando ciclo para evitar queima de proxies/sessões.")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="circuit_breaker", simulated=False, error="circuit_open"
            )
        
        # --- CONFIGURAÇÃO IMUTÁVEL POR CICLO (Fase 4: SRE Anti-Race Condition) ---
        current_cycle_config = dict(self.config)
        
        # 🛡️ HIBERNAÇÃO INTELIGENTE (PASA v65.1)
        if self.consecutive_blocks >= 3:
            hibernation_time = 3600 # 1 hora
            self.logger.warning(f"🛌 [V2] Detectados {self.consecutive_blocks} bloqueios seguidos. Hibernando por {hibernation_time//60} min...")
            await asyncio.sleep(hibernation_time)
            self.consecutive_blocks = 0 # Reseta após hibernar

        # 🧹 CLEANUP DE PROCESSOS (Épico 1)
        if self.cycle % 10 == 0:
            cleanup_orphans()

        # 📦 SINCRONIZAÇÃO DE BACKGROUND (SQLite -> Supabase)
        if self.cycle % 5 == 0:
            synced = await local_buffer.sync_with_supabase(self.db)
            if synced: self.logger.info(f"🔄 [V2] Sincronizados {synced} registros pendentes do SQLite.")

        self.seen_targets.clear()
        self.seen_queue_ids.clear()
        result = None # Inicializa para o finally

        # 🗡️ SELEÇÃO ATÔMICA (PASA v88.0 - Fase 8.3)
        # Usa SELECT FOR UPDATE SKIP LOCKED quando disponível para suporte horizontal.
        # Fallback automático para o método legado se a migração SQL ainda não foi aplicada.
        target = None
        use_atomic = getattr(self.queue, 'claim_next_target_atomic', None) is not None

        if use_atomic:
            target = await self.queue.claim_next_target_atomic(
                worker_id=self.worker_id,
                seen_targets=self.seen_targets,
                active_targets=getattr(self, 'active_targets', None),
            )
        else:
            if hasattr(self, "claim_lock"):
                async with self.claim_lock:
                    target = await self.queue.claim_next_target(
                        current_cycle_config, self.seen_queue_ids, self.seen_targets,
                        active_targets=getattr(self, "active_targets", None),
                    )
            else:
                target = await self.queue.claim_next_target(
                    current_cycle_config, self.seen_queue_ids, self.seen_targets,
                    active_targets=getattr(self, "active_targets", None),
                )

        if not target:
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="no_target", simulated=False, error="no_tasks_available"
            )

        self.logger.info(f"🔄 [V2] Ciclo {self.cycle} | Alvo: @{target.username}")
        
        # 🧠 INTEGRAÇÃO DE INTELIGÊNCIA (v84.15): Pesquisa antes de coletar se for novo
        try:
            # Verifica se precisa de validação de identidade ou dados básicos
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

        # 💾 CHECKPOINT INTRA-CYCLE (PASA v88.0 - Fase 8.5)
        # Carrega checkpoint existente para retomar do último post após crash.
        checkpoint = CheckpointManager(
            db_client=self.db,
            worker_id=self.worker_id,
            candidato_id=target.username,
        )
        previous_cp = await checkpoint.load()
        resume_from_shortcode = previous_cp.get('last_shortcode') if previous_cp else None
        if resume_from_shortcode:
            self.logger.info(
                "🔃 [V2] Retomando ciclo de @%s a partir do post %s (checkpoint encontrado).",
                target.username, resume_from_shortcode,
            )

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0

        # Callback assíncrona para persistência incremental
        async def handle_post_scraped(shortcode: str, post_comments: List[Dict[str, Any]]):
            nonlocal inserted_total, duplicated_total, comments_count
            if not post_comments:
                return

            comments_count += len(post_comments)

            # ♻️ FILTRO LÉXICO (Pre-AI) - PASA v65.0
            filtered_comments = lexical_filter.filter_list(post_comments)
            
            # 🤖 DETECÇÃO DE COMPORTAMENTO COORDENADO (v71.0)
            from core.behavior_engine import behavior_engine
            filtered_comments = behavior_engine.detect_coordinated_clusters(filtered_comments)

            if not filtered_comments:
                duplicated_total += len(post_comments)
                return

            # Filtra campos para garantir que apenas colunas existentes sejam enviadas
            safe_comments = []
            now = datetime.now(timezone.utc).isoformat()
            for c in filtered_comments:
                safe_c = {
                    "id_externo": c.get("id_externo"),
                    "texto_bruto": c.get("texto_bruto"),
                    "autor_username": c.get("autor_username"),
                    "data_publicacao": c.get("data_publicacao") or now,
                    "data_coleta": c.get("data_coleta") or now,
                    "candidato_id": c.get("candidato_id") or target.username,
                    "post_shortcode": c.get("post_shortcode") or shortcode,
                    "plataforma": c.get("plataforma") or "INSTAGRAM",
                    "processado_ia": False,
                    "tier_used": c.get("tier_used") or 2
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
                    on_conflict="candidato_id,post_shortcode,id_externo",
                    ignore_duplicates=True
                ).execute()
                
                if res.data:
                    inserted = len(res.data)
                    inserted_total += inserted
                    duplicated_total += len(post_comments) - inserted
            except Exception as e_upsert:
                # 🆘 SALVAMENTO DE EMERGÊNCIA (v63.0): Fallback para Schema Mismatch
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
                        on_conflict="candidato_id,post_shortcode,id_externo",
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

            # 💾 SALVAMENTO DE CHECKPOINT POR POST (Fase 8.5)
            posts_done = previous_cp.get('posts_done', 0) + 1 if previous_cp else 1
            await checkpoint.save(
                last_shortcode=shortcode,
                posts_done=posts_done,
                comments_done=inserted_total,
            )
            self.logger.info(f"💾 [V2] Checkpoint intermediário salvo para post {shortcode} (+{inserted} novos comentários).")

        try:
            # 1. Scraping com callback assíncrona
            scrape_data = await self.scraper.scrape_profile(
                username=target.username,
                candidato_id=target.candidato_id,
                max_posts=current_cycle_config.get('max_posts', 3),
                max_comments_per_post=100,
                resume_after_shortcode=resume_from_shortcode,  # Fase 8.5: retomada
                on_post_scraped=handle_post_scraped,
            )
            
            # Sucesso técnico no scrape -> Reseta contador de bloqueios
            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("instagram")
            
            if isinstance(scrape_data, dict):
                target.post_metas = scrape_data.get("post_metas", [])
            else:
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
            stats = self.scraper.get_stats()

            if comments_count == 0:
                if stats.get("junk_detected", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Apenas lixo detectado para @{target.username}. Sinalizando falha de extração.")
                    result = CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, simulated=False, error="junk_detected"
                    )
                    return result
                # Se o scraper retornou vazio mas não levantou erro, pode ser apenas falta de conteúdo
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, error="no_comments_found"
                )
                return result

            # Como a persistência incremental já foi concluída na callback,
            # nós apenas reportamos as estatísticas acumuladas do ciclo.
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

            # Ciclo completo com sucesso: limpa checkpoint
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
            # PASA v58.2: Injeta erro no alvo para que o rotate_target decida pela hibernação
            if isinstance(result, dict) and result.get("error"):
                target.error = result.get("error")
            elif hasattr(result, "error") and result.error:
                target.error = result.error

            # PASA v88.0 (Fase 8.3): Release atômico do lock se foi claimado atomicamente
            if target and getattr(target, 'source', '') == 'fila_coleta_atomic' and target.queue_id:
                # PASA v88.2: Ativa a classificação de temperatura (termômetro) antes de liberar
                await self.queue.update_target_metrics(target)
                
                final_status = "CONCLUIDO"
                if hasattr(result, 'error') and result.error:
                    err = result.error
                    if err in ('junk_detected', 'invalid_target: 404_not_found'):
                        final_status = 'SEM_DADOS_RECENTES'
                    elif err in ('all_sessions_blocked', 'shutdown_requested'):
                        final_status = 'PENDENTE'  # Recoloca na fila para reprocessar
                    else:
                        final_status = 'FALHA'
                try:
                    await self.queue.release_atomic(target.queue_id, final_status, self.worker_id)
                except Exception as e_rel:
                    logger.warning("[V2] Falha no release atômico: %s", e_rel)
            else:
                # Legado: usa rotate_target para atualizar o status
                await self.queue.rotate_target(target)

