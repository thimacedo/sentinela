# workers/ai/sa_revisao_online.py
from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, Optional

from core.ai_service import ai_service
from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult

logger = logging.getLogger("SaRevisaoOnline")

class SaRevisaoOnline(BaseSubAgent):
    """
    Subagente: SaRevisaoOnline — Revisão Online de Comentários Suspeitos (PASA v89.0)
    ══════════════════════════════════════════════════════════════════════════════
    Este subagente roda como uma fila secundária, independente do fluxo principal.
    Ele consome comentários marcados como "SUSPEITO" pelo Ollama local e os reclassifica
    utilizando a malha de provedores de IA Cloud (Mistral, Groq, etc.).
    
    Garante que:
      - A classificação primária de triagem rápida (Ollama) e a coleta não sofram atrasos.
      - A classificação profunda MCA v2.2 (nuvem) ocorra de forma assíncrona e isolada.
    """

    def __init__(self, worker_id: str = "sa-revisao-online-01", config: Optional[dict] = None):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.batch_size = cfg.get("batch_size", 50)

    def describe(self) -> str:
        return "SaRevisaoOnline — Revisão analítica na nuvem de comentários marcados como suspeitos"

    async def setup(self) -> None:
        await super().setup()
        logger.info(f"🚀 SaRevisaoOnline {self.worker_id} pronto para revisão analítica cloud.")

    async def teardown(self) -> None:
        await super().teardown()
        logger.info(f"🛑 SaRevisaoOnline {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.warning(f"🛑 [{self.worker_id}] Interrupção detectada! Abortando ciclo {self.cycle}...")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="sa_revisao_online", error="shutdown_requested",
                duration=asyncio.get_event_loop().time() - start_time
            )

        logger.info(f"🧠 [{self.worker_id}] Ciclo {self.cycle} | Buscando comentários SUSPEITOS para revisão cloud...")
        
        try:
            # Executa a revisão online na fila secundária
            reviewed_count = await ai_service.run_batch_online_review(limit=self.batch_size)
            
            if reviewed_count == 0:
                logger.info(f"✅ [{self.worker_id}] Fila secundária vazia. Sem comentários SUSPEITOS para revisar.")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle,
                    target="backlog_revisao", source="sa_revisao_online", extracted=0, simulated=False,
                    error="no_tasks_available", duration=asyncio.get_event_loop().time() - start_time
                )

            logger.info(f"✨ [{self.worker_id}] Revisão concluída: {reviewed_count} comentários classificados na nuvem.")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target="backlog_revisao", source="sa_revisao_online",
                extracted=reviewed_count,
                inserted=0,
                duplicated=0,
                classified=reviewed_count,
                db_success=True,
                classifier_success=True,
                simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )

        except Exception as e:
            logger.error(f"💥 Erro no SaRevisaoOnline: {e}")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )
