from __future__ import annotations

import logging
import asyncio
import time
from typing import Dict, Any

from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.local_buffer import local_buffer
from core.lexical_filter import lexical_filter
from core.checkpoint_manager import CheckpointManager
from core.event_bus import local_bus
from core.circuit_breaker import scraper_circuit_breaker
from core.ai_service import ai_service
from core.agent_scraper.agent_stealth import StealthAgentOODA
from instagram_scraper.scrape_stealth import StealthEngine

logger = logging.getLogger("worker.ai.sa_ig_stealth")

class SaInstagramStealth(BaseSubAgent):
    """
    Subagente Autônomo para o Motor Legado (Stealth/Instaloader).
    Encapsula as lógicas antigas num loop OODA inteligente, conectando-se ao Sentinela.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        
        # O motor principal
        self.scraper = StealthEngine(config_path="config/config.json")
        self.scraper.config["headless"] = False  # [DEBUG] Força GUI visível para diagnosticar login
        self.agent = StealthAgentOODA(scraper_instance=self.scraper, ai_service=ai_service)
    def describe(self) -> str:
        return "Instagram Stealth Agent (OODA) - Compatibilidade Legada Autônoma"

    async def setup(self) -> None:
        await super().setup()
        logger.info(f"🚀 SubAgente {self.worker_id} (Stealth) configurado.")
        # Inicializa driver no pool de threads se configurado
        await asyncio.to_thread(self.scraper.init_driver)
        
    async def teardown(self) -> None:
        logger.info(f"🛑 Desligando SubAgente {self.worker_id}")
        await asyncio.to_thread(self.scraper.close)
        await super().teardown()

    async def _process_target(self, target: str) -> None:
        """Lida com a extração e OODA para um alvo específico"""
        logger.info(f"[{self.worker_id}] Iniciando alvo OODA: {target}")
        
        # OODA Cycle
        context = {"target": target}
        
        # Envia notificação oficial ntfy pelo EventBus
        from core.event_bus import EventBus
        EventBus().notify(
            title="Agente Stealth Operando",
            message=f"Iniciando ciclo OODA para alvo: {target}",
            tags="robot,mag",
            priority="default"
        )
        
        decision_result = await self.agent.run_cycle(context)
        
        if decision_result.get("tool") == "fallback_to_instaloader":
            # Aciona Instaloader via CPU-bound thread para evitar block
            from instagram_scraper.scrape_instaloader import InstaloaderEngine
            engine = InstaloaderEngine()
            # Simulamos a execução (apenas exemplo)
            logger.info("Executando fallback instaloader...")
            return

        # Caminho Feliz Stealth
        # Chama scraper_targets em thread IO bound
        comments = await self.run_io_bound(self.scraper.scrape_targets, [target], 1)
        
        for c in comments:
            filtered = await lexical_filter.evaluate_content_async(
                text=c.get("text", ""),
                metadata={"username": c.get("username"), "target": target}
            )
            c["classification"] = filtered.classification
            c["sentiment"] = filtered.sentiment
            c["severity_score"] = filtered.severity_score
            
            # Persistência Zero Loss Policy
            await local_buffer.insert_record("instagram_comments", c)
            
        local_bus.publish("NEW_DATA_AVAILABLE", {"source": "sa_ig_stealth", "count": len(comments)})
        
    async def run_cycle(self) -> CycleResult:
        """Puxa tarefas da fila e aplica resiliência (Circuit Breaker/Checkpoint)"""
        if not scraper_circuit_breaker.can_execute("instagram_stealth"):
            logger.warning("Circuit Breaker aberto, abortando ciclo stealth.")
            return CycleResult(worker_id=self.worker_id, cycle=0, error="Circuit_Breaker_Open", failed=1)

        target_obj = await self.queue.claim_next_target_atomic(self.worker_id)
        if not target_obj:
            return CycleResult(worker_id=self.worker_id, cycle=0, target=None)

        target = target_obj.username
        
        try:
            # Login OODA se necessário
            if not self.scraper.logged_in:
                await asyncio.to_thread(self.scraper.login)
                
            await self._process_target(target)
            
            # Pacing Estratégico (Consistência > Velocidade)
            # O agente pausa aleatoriamente entre os alvos para mimetizar comportamento humano
            import random
            pacing_delay = random.uniform(15.0, 45.0)
            logger.info(f"Pacing ativo: aguardando {pacing_delay:.1f}s antes de concluir o ciclo para evitar rate limit do Instagram.")
            await asyncio.sleep(pacing_delay)
            
            # Marca tarefa como concluída
            if getattr(target_obj, 'queue_id', None):
                await self.queue.release_atomic(target_obj.queue_id, "CONCLUIDO", self.worker_id)
            return CycleResult(worker_id=self.worker_id, cycle=0, target=target, db_success=True)
            
        except Exception as e:
            scraper_circuit_breaker.record_failure("instagram_stealth", str(e))
            logger.error(f"Erro em {target}: {e}")
            if getattr(target_obj, 'queue_id', None):
                await self.queue.release_atomic(target_obj.queue_id, "FALHA", self.worker_id)
            return CycleResult(worker_id=self.worker_id, cycle=0, target=target, error=str(e), failed=1)
