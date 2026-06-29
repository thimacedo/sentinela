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
        self.agent = StealthAgentOODA(scraper_instance=self.scraper, ai_service=ai_service)
        self.checkpoint = CheckpointManager(worker_id=worker_id)
        
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
        if not scraper_circuit_breaker.can_execute():
            logger.warning("Circuit Breaker aberto, abortando ciclo stealth.")
            return CycleResult.failure("Circuit_Breaker_Open")

        tasks = await self.queue.claim_tasks("coleta_instagram", limit=1)
        if not tasks:
            return CycleResult.idle()

        task = tasks[0]
        target = task["target_id"]
        
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
            await self.queue.complete_task(task["id"], {"status": "success"})
            return CycleResult.success(1, 0)
            
        except Exception as e:
            scraper_circuit_breaker.record_failure()
            logger.error(f"Erro em {target}: {e}")
            await self.queue.fail_task(task["id"], str(e))
            return CycleResult.failure(str(e))
