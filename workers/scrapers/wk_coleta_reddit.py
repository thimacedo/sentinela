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
    import asyncpraw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

logger = logging.getLogger("worker.reddit")

class WkColetaReddit(BaseWorker):
    """
    Worker especializado na coleta do Reddit via API PRAW.
    Substitui a infraestrutura pesada baseada em proxies e scraping visual.
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
        
        self.reddit = None
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "SentinelaDemocratica/1.0")

        if not PRAW_AVAILABLE:
            self.logger.error("Biblioteca 'asyncpraw' não está instalada. O worker não funcionará corretamente.")

    def describe(self) -> str:
        return "Reddit Scraper V1 - Coleta Leve via API PRAW"

    async def setup(self) -> None:
        self.logger.info(f"🚀 Worker {self.worker_id} (Reddit) configurado.")
        await local_buffer.sync_with_supabase(self.db)
        
        if PRAW_AVAILABLE and self.client_id and self.client_secret:
            try:
                self.reddit = asyncpraw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.logger.info("✅ [Reddit] Instância PRAW criada com sucesso.")
            except Exception as e:
                self.logger.error(f"❌ [Reddit] Falha ao configurar PRAW: {e}")

    async def teardown(self) -> None:
        if self.reddit:
            await self.reddit.close()
        self.logger.info(f"🛑 Worker {self.worker_id} (Reddit) encerrado.")

    async def run_cycle(self) -> CycleResult:
        if not PRAW_AVAILABLE or not self.reddit:
            await asyncio.sleep(60)
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="reddit_engine", error="auth_missing")

        if time.time() - self.last_activity > 600:
            self.logger.warning("🚨 [Heartbeat] Scraper inativo por > 10min. Forçando reset do lock e rotação.")
            self.last_activity = time.time()
            if hasattr(self, 'current_target') and getattr(self, 'current_target', None):
                 await self.queue.rotate_target(self.current_target)

        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        if not scraper_circuit_breaker.can_execute("reddit"):
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
        self.logger.info(f"🔄 [Reddit] Ciclo {self.cycle} | Alvo: @{target.username}")

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0
        error_reason = None

        try:
            # Busca as palavras-chave no JSONB
            cand_data = await asyncio.to_thread(
                self.db.table("candidatos").select("redes_sociais").eq("username", target.username).single().execute
            )
            keywords_list = cand_data.data.get("redes_sociais", {}).get("reddit_keywords") if cand_data and cand_data.data else None
            
            search_query = keywords_list[0] if keywords_list and len(keywords_list) > 0 else target.username
            self.logger.info(f"🔎 [Reddit] Buscando termo: {search_query}")

            # Busca nas threads de subreddits políticos
            subreddit = await self.reddit.subreddit("brasil+brasilivre+politica")
            submissions = subreddit.search(search_query, sort="new", time_filter="month", limit=5)
            
            extracted_items = []
            
            async for submission in submissions:
                # Extrai os dados do post principal
                extracted_items.append({
                    "id_externo": submission.id,
                    "texto_bruto": f"[{submission.title}] {submission.selftext}",
                    "autor_username": submission.author.name if submission.author else "deleted",
                    "post_shortcode": submission.id,
                    "candidato_id": target.username,
                    "plataforma": "REDDIT",
                    "data_publicacao": datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
                    "data_coleta": datetime.now(timezone.utc).isoformat(),
                    "processado_ia": False,
                    "tier_used": 2
                })
                
                # Extrai os comentários principais
                await submission.comments.replace_more(limit=0) # Evita chamadas recursivas pesadas
                for comment in submission.comments:
                    extracted_items.append({
                        "id_externo": comment.id,
                        "texto_bruto": comment.body,
                        "autor_username": comment.author.name if comment.author else "deleted",
                        "post_shortcode": submission.id,
                        "candidato_id": target.username,
                        "plataforma": "REDDIT",
                        "data_publicacao": datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
                        "data_coleta": datetime.now(timezone.utc).isoformat(),
                        "processado_ia": False,
                        "tier_used": 2
                    })

            comments_count = len(extracted_items)
            
            if comments_count == 0:
                error_reason = "no_comments_found"
                raise ValueError("no_comments_found")

            # Filtragem Léxica Básica
            filtered_comments = lexical_filter.filter_list(extracted_items)
            
            # Detecção de Comportamento Coordenado
            try:
                from core.behavior_engine import behavior_engine
                filtered_comments = await behavior_engine.detect_coordinated_clusters(filtered_comments)
            except Exception as e:
                self.logger.warning(f"⚠️ [Reddit] Falha na detecção de bots: {e}")

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
                        self.logger.info(f"⚡ [EventBus] Sinalizando AIProcessorWorker: {inserted} novos registros do Reddit.")
                        local_bus.signal_new_data()
                        
                except Exception as e_upsert:
                    self.logger.error(f"❌ [Reddit] Erro na inserção Supabase: {e_upsert}")

            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("reddit")

        except Exception as e:
            if "no_comments_found" not in str(e):
                self.consecutive_blocks += 1
                scraper_circuit_breaker.record_failure("reddit", error_msg=str(e))
                self.logger.error(f"⚠️ [Reddit] Erro inesperado na extração: {e}")
            
            if not error_reason:
                error_reason = str(e)

        try:
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="reddit_engine",
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
                    logger.warning("[Reddit] Falha no release atômico: %s", e_rel)
            else:
                await self.queue.rotate_target(target)
