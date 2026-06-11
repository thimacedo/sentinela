from __future__ import annotations

import logging
import asyncio
import os
import time
from typing import List, Dict
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
            await asyncio.sleep(3600)
            self.consecutive_blocks = 0

        # 🌙 MODO NOTURNO
        current_hour = datetime.now().hour
        if current_hour >= 23 or current_hour < 5:
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
        
        # ... (rest of logic)
        result = CycleResult(worker_id=self.worker_id, cycle=self.cycle, target=target.username, source="v2_engine", extracted=0, db_success=True)
        await self.queue.rotate_target(target)
        return result
