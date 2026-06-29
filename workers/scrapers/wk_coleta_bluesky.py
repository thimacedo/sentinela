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
from core.ai_service import clean_null_chars

from core.local_buffer import local_buffer
from core.lexical_filter import lexical_filter
from core.event_bus import local_bus
from core.circuit_breaker import scraper_circuit_breaker

try:
    from atproto import AsyncClient
    ATPROTO_AVAILABLE = True
except ImportError:
    ATPROTO_AVAILABLE = False

logger = logging.getLogger("worker.bluesky")

class WkColetaBluesky(BaseWorker):
    """
    Worker especializado na coleta da rede Bluesky via API AT Protocol (atproto).
    Substitui a infraestrutura pesada baseada em DOM/Playwright por requisições REST/JSON.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.consecutive_blocks = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self.last_activity = time.time()
        
        self.client = None
        self.authenticated = False
        self.bsky_user = os.getenv("BSKY_USER")
        self.bsky_pass = os.getenv("BSKY_PASS")

        if not ATPROTO_AVAILABLE:
            self.logger.error("Biblioteca 'atproto' não está instalada. O worker não funcionará corretamente.")

    def describe(self) -> str:
        return "Bluesky Scraper V1 - Coleta Leve via API atproto"

    async def setup(self) -> None:
        self.logger.info(f"🚀 Worker {self.worker_id} (Bluesky) configurado.")
        await local_buffer.sync_with_supabase(self.db)
        
        if ATPROTO_AVAILABLE and self.bsky_user and self.bsky_pass:
            try:
                self.client = AsyncClient()
                await self.client.login(self.bsky_user, self.bsky_pass)
                self.authenticated = True
                self.logger.info("✅ [Bluesky] Autenticação realizada com sucesso.")
            except Exception as e:
                self.logger.error(f"❌ [Bluesky] Falha na autenticação inicial: {e}")

    async def teardown(self) -> None:
        self.logger.info(f"🛑 Worker {self.worker_id} (Bluesky) encerrado.")

    async def run_cycle(self) -> CycleResult:
        if not ATPROTO_AVAILABLE or not self.authenticated:
            await asyncio.sleep(60)
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="bluesky_engine", error="auth_missing")

        if time.time() - self.last_activity > 600:
            self.logger.warning("🚨 [Heartbeat] Scraper inativo por > 10min. Forçando reset do lock e rotação.")
            self.last_activity = time.time()
            if hasattr(self, 'current_target') and getattr(self, 'current_target', None):
                 await self.queue.rotate_target(self.current_target)

        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        if not scraper_circuit_breaker.can_execute("bluesky"):
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="circuit_breaker", simulated=False, error="circuit_open")
        
        current_cycle_config = dict(self.config)
        
        if self.consecutive_blocks >= 3:
            await asyncio.sleep(3600)
            self.consecutive_blocks = 0

        if self.cycle % 5 == 0:
            await local_buffer.sync_with_supabase(self.db)

        self.seen_targets.clear()
        self.seen_queue_ids.clear()
        
        target = await self.queue.claim_next_target_atomic(
            self.worker_id, self.seen_targets, active_targets=getattr(self, 'active_targets', None)
        )

        if not target:
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="no_target", simulated=False, error="no_tasks_available")

        self.last_activity = time.time()
        self.current_target = target
        self.logger.info(f"🔄 [Bluesky] Ciclo {self.cycle} | Alvo: @{target.username}")

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0
        error_reason = None

        try:
            # Busca o handle exato no JSONB
            cand_data = await asyncio.to_thread(
                self.db.table("candidatos").select("redes_sociais").eq("username", target.username).single().execute
            )
            saved_handle = cand_data.data.get("redes_sociais", {}).get("bluesky") if cand_data and cand_data.data else None

            if saved_handle:
                # Pula a busca e usa o handle validado
                self.logger.info(f"🔎 [Bluesky] Usando handle do banco: {saved_handle}")
                actor_handle = saved_handle
            else:
                # 1. Busca do perfil (Search Actor)
                search_resp = await self.client.app.bsky.actor.search_actors({'term': target.username, 'limit': 3})
                
                if not search_resp or not search_resp.actors:
                    self.logger.warning(f"⚠️ [Bluesky] Perfil não encontrado para o alvo: {target.username}")
                    error_reason = "invalid_target: 404_not_found"
                    raise ValueError("invalid_target")

                actor = search_resp.actors[0]
                actor_handle = actor.handle
                self.logger.info(f"🔎 [Bluesky] Encontrado via busca: {actor.display_name} (@{actor_handle})")

            # 2. Extração do Feed (getAuthorFeed)
            feed_resp = await self.client.app.bsky.feed.get_author_feed({'actor': actor_handle, 'limit': 20})
            
            extracted_items = []
            for item in feed_resp.feed:
                post = item.post
                if not hasattr(post, 'record') or not hasattr(post.record, 'text'):
                    continue
                    
                uri = getattr(post, 'uri', '')
                shortcode = uri.split("/")[-1] if "/" in uri else uri
                
                extracted_items.append({
                    "id_externo": getattr(post, 'cid', ''),
                    "texto_bruto": post.record.text,
                    "autor_username": post.author.handle if hasattr(post, 'author') else '',
                    "post_shortcode": shortcode,
                    "candidato_id": target.username,
                    "plataforma": "BLUESKY",
                    "data_publicacao": getattr(post.record, 'created_at', None) or datetime.now(timezone.utc).isoformat(),
                    "data_coleta": datetime.now(timezone.utc).isoformat(),
                    "processado_ia": False,
                    "tier_used": 2
                })

            comments_count = len(extracted_items)
            
            if comments_count == 0:
                error_reason = "no_comments_found"
                raise ValueError("no_comments_found")

            # 3. Filtragem Léxica Básica
            filtered_comments = lexical_filter.filter_list(extracted_items)
            
            # 4. Detecção de Comportamento Coordenado
            try:
                from core.behavior_engine import behavior_engine
                filtered_comments = await behavior_engine.detect_coordinated_clusters(filtered_comments)
            except Exception as e:
                self.logger.warning(f"⚠️ [Bluesky] Falha na detecção de bots, prosseguindo com fluxo normal: {e}")

            if not filtered_comments:
                duplicated_total += comments_count
            else:
                safe_comments = []
                for c in filtered_comments:
                    if c.get("is_bot"):
                        c["analise_pericial"] = f"[BOT DETECTED] Padrão: {c.get('bot_pattern')}"
                        c["categoria_ia"] = "CAMPANHA_COORDENADA"
                    safe_comments.append(c)

                # Salva localmente
                local_buffer.save(safe_comments)

                try:
                    res = self.db.table("comentarios").upsert(
                        clean_null_chars(safe_comments), 
                        on_conflict="candidato_id,post_shortcode,id_externo",
                        ignore_duplicates=True
                    ).execute()
                    
                    inserted = len(res.data) if res.data else 0
                    inserted_total += inserted
                    duplicated_total += comments_count - inserted
                    
                    if inserted > 0:
                        self.logger.info(f"⚡ [EventBus] Sinalizando AIProcessorWorker: {inserted} novos registros do Bluesky.")
                        local_bus.signal_new_data()
                        
                except Exception as e_upsert:
                    self.logger.error(f"❌ [Bluesky] Erro na inserção Supabase: {e_upsert}")

            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("bluesky")

        except Exception as e:
            if "invalid_target" not in str(e) and "no_comments_found" not in str(e):
                self.consecutive_blocks += 1
                scraper_circuit_breaker.record_failure("bluesky", error_msg=str(e))
                self.logger.error(f"⚠️ [Bluesky] Erro inesperado na extração: {e}")
            
            if not error_reason:
                error_reason = str(e)

        try:
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="bluesky_engine",
                extracted=comments_count,
                inserted=inserted_total,
                duplicated=duplicated_total,
                db_success=inserted_total > 0,
                simulated=False,
                error=error_reason if comments_count == 0 else None,
                duration=asyncio.get_event_loop().time() - start_time
            )
            return result

        except Exception as e:
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )
        finally:
            if hasattr(target, 'error') and not target.error:
                target.error = error_reason

            if target and getattr(target, 'source', '') == 'fila_coleta_atomic' and target.queue_id:
                await self.queue.update_target_metrics(target)
                
                final_status = "CONCLUIDO"
                if error_reason:
                    if error_reason in ('invalid_target: 404_not_found'):
                        final_status = 'SEM_DADOS_RECENTES'
                    else:
                        final_status = 'FALHA'
                try:
                    await self.queue.release_atomic(target.queue_id, final_status, self.worker_id)
                except Exception as e_rel:
                    logger.warning("[Bluesky] Falha no release atômico: %s", e_rel)
            else:
                await self.queue.rotate_target(target)
