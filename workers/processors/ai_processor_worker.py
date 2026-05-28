from __future__ import annotations
import logging
import asyncio
from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.ai_service import ai_service

logger = logging.getLogger("worker.ai_processor")

class AIProcessorWorker(BaseWorker):
    """
    Worker: AIProcessor (Perícia PASA Assíncrona)
    Finalidade: Consumir o backlog de comentários não processados pela IA.
    Desacopla a coleta (Scraping) da análise (IA).
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.batch_size = config.get("batch_size", 100)

    def describe(self) -> str:
        return "AI Processor Worker - Classificação PASA em Lote"

    async def setup(self) -> None:
        logger.info(f"🚀 AIProcessorWorker {self.worker_id} pronto para perícia.")

    async def teardown(self) -> None:
        logger.info(f"🛑 AIProcessorWorker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.warning(f"🛑 [AI] Interrupção detectada! Abortando ciclo {self.cycle}...")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="ai_processor", error="shutdown_requested",
                duration=asyncio.get_event_loop().time() - start_time
            )

        logger.info(f"🧠 [AI] Ciclo {self.cycle} | Processando lote de {self.batch_size}...")
        
        try:
            # Executa a classificação em lote
            # O ai_service já gerencia a seleção de itens processado_ia=False
            classified_count = await ai_service.run_batch_classification(limit=self.batch_size)
            
            if classified_count == 0:
                logger.info("✅ Fila de IA vazia. Aguardando novos dados.")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle,
                    target="backlog_ia", source="ai_processor", extracted=0, simulated=False, 
                    error="no_tasks_available", duration=asyncio.get_event_loop().time() - start_time
                )

            logger.info(f"✨ [AI] Sucesso: {classified_count} comentários periciados.")
            
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target="backlog_ia", source="ai_processor",
                extracted=classified_count, # Usamos extracted para representar o processamento
                inserted=0,
                duplicated=0,
                classified=classified_count,
                db_success=True,
                classifier_success=True,
                simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )

        except Exception as e:
            logger.error(f"💥 Erro no AIProcessorWorker: {e}")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )
