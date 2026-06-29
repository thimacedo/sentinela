from __future__ import annotations

import logging
import asyncio
import os
import time
import httpx
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

logger = logging.getLogger("worker.twitter")

class WkColetaTwitter(BaseWorker):
    """
    Worker especializado na coleta da rede X (Twitter) via API Xquik.
    Coleta tweets publicados pelos candidatos e persiste no buffer de processamento do Sentinela.
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
        
        self.authenticated = False
        self.xquik_api_key = os.getenv("XQUIK_API_KEY")

        if not self.xquik_api_key:
            self.logger.error("Chave 'XQUIK_API_KEY' não está configurada no .env. O worker do Twitter/X não iniciará corretamente.")
        else:
            self.authenticated = True

    def describe(self) -> str:
        return "Twitter/X Scraper V1 - Coleta Leve via API Xquik"

    async def setup(self) -> None:
        self.logger.info(f"🚀 Worker {self.worker_id} (Twitter/X) configurado.")
        await local_buffer.sync_with_supabase(self.db)

    async def teardown(self) -> None:
        self.logger.info(f"🛑 Worker {self.worker_id} (Twitter/X) encerrado.")

    async def _fetch_tweets(self, username: str) -> List[Dict[str, Any]]:
        url = "https://xquik.com/api/v1/x/tweets/search"
        headers = {
            "x-api-key": self.xquik_api_key,
            "Content-Type": "application/json"
        }
        params = {
            "query": f"from:{username}",
            "limit": self.config.get("max_tweets", 20)
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code in (401, 403):
                self.logger.error(f"❌ [Twitter] Erro de autenticação na API Xquik: {resp.status_code}")
                self.authenticated = False
                raise ValueError("xquik_auth_error")
            elif resp.status_code == 429:
                self.logger.warning("⚠️ [Twitter] Rate limit atingido na API Xquik (429).")
                raise ValueError("xquik_rate_limit")
            elif resp.status_code != 200:
                self.logger.error(f"❌ [Twitter] Erro na API Xquik: {resp.status_code} - {resp.text}")
                raise ValueError(f"xquik_api_error_{resp.status_code}")
                
            data = resp.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("data") or data.get("tweets") or data.get("results") or []
            return []

    async def run_cycle(self) -> CycleResult:
        if not self.authenticated or not self.xquik_api_key:
            await asyncio.sleep(60)
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="twitter_engine", error="auth_missing")

        if time.time() - self.last_activity > 600:
            self.logger.warning("🚨 [Heartbeat] Scraper Twitter inativo por > 10min. Forçando reset de lock.")
            self.last_activity = time.time()
            if hasattr(self, 'current_target') and getattr(self, 'current_target', None):
                 await self.queue.rotate_target(self.current_target)

        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        if not scraper_circuit_breaker.can_execute("twitter"):
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="circuit_breaker", simulated=False, error="circuit_open")
        
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
        self.logger.info(f"🔄 [Twitter] Ciclo {self.cycle} | Alvo: @{target.username}")

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0
        error_reason = None

        try:
            # 1. Recupera identificador do Twitter no cadastro do candidato
            cand_data = await asyncio.to_thread(
                self.db.table("candidatos").select("redes_sociais").eq("username", target.username).single().execute
            )
            
            saved_handle = None
            if cand_data and cand_data.data:
                redes = cand_data.data.get("redes_sociais") or {}
                saved_handle = redes.get("twitter") or redes.get("x")

            twitter_username = saved_handle if saved_handle else target.username
            self.logger.info(f"🔎 [Twitter] Buscando tweets para actor: @{twitter_username}")

            # 2. Executa chamada na API
            tweets = await self._fetch_tweets(twitter_username)
            
            extracted_items = []
            for item in tweets:
                tweet_id = str(item.get("id") or item.get("id_str") or item.get("id_externo") or "")
                if not tweet_id:
                    continue
                    
                text = item.get("text") or item.get("full_text") or item.get("texto_bruto") or ""
                author = item.get("username") or item.get("user", {}).get("screen_name") or item.get("author_username") or twitter_username
                pub_date = item.get("created_at") or item.get("data_publicacao") or datetime.now(timezone.utc).isoformat()
                
                extracted_items.append({
                    "id_externo": tweet_id,
                    "texto_bruto": text,
                    "autor_username": author,
                    "post_shortcode": tweet_id,
                    "candidato_id": target.username,
                    "plataforma": "TWITTER",
                    "data_publicacao": pub_date,
                    "data_coleta": datetime.now(timezone.utc).isoformat(),
                    "processado_ia": False,
                    "tier_used": 2
                })

            comments_count = len(extracted_items)
            
            if comments_count == 0:
                error_reason = "no_comments_found"
                raise ValueError("no_comments_found")

            # 3. Filtragem Léxica Básica local
            filtered_comments = lexical_filter.filter_list(extracted_items)
            
            # 4. Detecção de Comportamento Coordenado
            try:
                from core.behavior_engine import behavior_engine
                filtered_comments = behavior_engine.detect_coordinated_clusters(filtered_comments)
            except Exception as e:
                self.logger.warning(f"⚠️ [Twitter] Falha na detecção de bots, prosseguindo com fluxo normal: {e}")

            if not filtered_comments:
                duplicated_total += comments_count
            else:
                safe_comments = []
                for c in filtered_comments:
                    if c.get("is_bot"):
                        c["analise_pericial"] = f"[BOT DETECTED] Padrão: {c.get('bot_pattern')}"
                        c["categoria_ia"] = "CAMPANHA_COORDENADA"
                    safe_comments.append(c)

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
                        self.logger.info(f"⚡ [EventBus] Sinalizando AIProcessorWorker: {inserted} novos registros do Twitter/X.")
                        local_bus.signal_new_data()
                        
                except Exception as e_upsert:
                    self.logger.error(f"❌ [Twitter] Erro na inserção Supabase: {e_upsert}")

            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("twitter")

        except Exception as e:
            if "invalid_target" not in str(e) and "no_comments_found" not in str(e):
                self.consecutive_blocks += 1
                scraper_circuit_breaker.record_failure("twitter", error_msg=str(e))
                self.logger.error(f"⚠️ [Twitter] Erro inesperado na extração: {e}")
            
            if not error_reason:
                error_reason = str(e)

        try:
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="twitter_engine",
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
                    logger.warning("[Twitter] Falha no release atômico: %s", e_rel)
            else:
                await self.queue.rotate_target(target)
