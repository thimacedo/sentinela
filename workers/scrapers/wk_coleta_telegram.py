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
    from telethon import TelegramClient
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

logger = logging.getLogger("worker.telegram")

class WkColetaTelegram(BaseWorker):
    """
    Worker especializado na coleta do Telegram via API Telethon (MTProto).
    Lê canais e grupos públicos usando a sessão persistida ('discovery_session.session').
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
        self.api_id = os.getenv("TG_API_ID")
        self.api_hash = os.getenv("TG_API_HASH")

        if not TELETHON_AVAILABLE:
            self.logger.error("Biblioteca 'telethon' não está instalada. O worker não funcionará corretamente.")

    def describe(self) -> str:
        return "Telegram Scraper V1 - Coleta Leve via API MTProto"

    async def setup(self) -> None:
        self.logger.info(f"🚀 Worker {self.worker_id} (Telegram) configurado.")
        await local_buffer.sync_with_supabase(self.db)
        
        if TELETHON_AVAILABLE and self.api_id and self.api_hash:
            try:
                # Usa a sessão já autorizada pelo script interativo
                self.client = TelegramClient('discovery_session', int(self.api_id), self.api_hash)
                await self.client.connect()
                if await self.client.is_user_authorized():
                    self.logger.info("✅ [Telegram] Autenticação da sessão realizada com sucesso.")
                else:
                    self.logger.error("❌ [Telegram] Sessão não autorizada. Rode 'python scripts/auth_telegram.py' primeiro.")
            except Exception as e:
                self.logger.error(f"❌ [Telegram] Falha ao configurar Telethon: {e}")

    async def teardown(self) -> None:
        if self.client:
            await self.client.disconnect()
        self.logger.info(f"🛑 Worker {self.worker_id} (Telegram) encerrado.")

    async def run_cycle(self) -> CycleResult:
        if not TELETHON_AVAILABLE or not self.client or not await self.client.is_user_authorized():
            await asyncio.sleep(60)
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="telegram_engine", error="auth_missing")

        if time.time() - self.last_activity > 600:
            self.logger.warning("🚨 [Heartbeat] Scraper inativo por > 10min. Forçando reset do lock e rotação.")
            self.last_activity = time.time()
            if hasattr(self, 'current_target') and getattr(self, 'current_target', None):
                 await self.queue.rotate_target(self.current_target)

        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        if not scraper_circuit_breaker.can_execute("telegram"):
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
        self.logger.info(f"🔄 [Telegram] Ciclo {self.cycle} | Alvo: @{target.username}")

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0
        error_reason = None

        try:
            # Busca o channel no JSONB
            cand_data = await asyncio.to_thread(
                self.db.table("candidatos").select("redes_sociais").eq("username", target.username).single().execute
            )
            saved_handle = cand_data.data.get("redes_sociais", {}).get("telegram") if cand_data and cand_data.data else None

            if not saved_handle:
                self.logger.warning(f"⚠️ [Telegram] Canal não encontrado no banco para o alvo: {target.username}")
                error_reason = "invalid_target: 404_not_found"
                raise ValueError("invalid_target")

            self.logger.info(f"🔎 [Telegram] Acessando canal: {saved_handle}")

            extracted_items = []
            
            # Busca as últimas 20 mensagens do canal
            async for message in self.client.iter_messages(saved_handle, limit=20):
                if not message.text:
                    continue
                    
                sender = await message.get_sender()
                sender_name = getattr(sender, 'username', None) or getattr(sender, 'title', 'Canal')
                
                extracted_items.append({
                    "id_externo": str(message.id),
                    "texto_bruto": message.text,
                    "autor_username": sender_name,
                    "post_shortcode": str(message.id),
                    "candidato_id": target.username,
                    "plataforma": "TELEGRAM",
                    "data_publicacao": message.date.astimezone(timezone.utc).isoformat(),
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
                self.logger.warning(f"⚠️ [Telegram] Falha na detecção de bots, prosseguindo com fluxo normal: {e}")

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
                        self.logger.info(f"⚡ [EventBus] Sinalizando AIProcessorWorker: {inserted} novos registros do Telegram.")
                        local_bus.signal_new_data()
                        
                except Exception as e_upsert:
                    self.logger.error(f"❌ [Telegram] Erro na inserção Supabase: {e_upsert}")

            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("telegram")

        except Exception as e:
            if "invalid_target" not in str(e) and "no_comments_found" not in str(e):
                self.consecutive_blocks += 1
                scraper_circuit_breaker.record_failure("telegram", error_msg=str(e))
                self.logger.error(f"⚠️ [Telegram] Erro inesperado na extração: {e}")
            
            if not error_reason:
                error_reason = str(e)

        try:
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="telegram_engine",
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
                    logger.warning("[Telegram] Falha no release atômico: %s", e_rel)
            else:
                await self.queue.rotate_target(target)
