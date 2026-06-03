from __future__ import annotations
import logging
import asyncio
from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.ai_service import ai_service

logger = logging.getLogger("worker.ai_processor")

class AIProcessorWorker(BaseWorker):
    """
    Worker: AIProcessor — Classificador Oficial do Pipeline PASA (PASA v88.0)
    ══════════════════════════════════════════════════════════════════════════
    ÚNICO classificador ativo em produção. O ClassifierWorker (Gemini direto)
    foi DEPRECIADO em v88.0 por não integrar a cascata de resiliência.

    Responsabilidades:
      1. Consumir o backlog de comentários não processados (processado_ia=False)
         via core/ai_service.py (cascata: Ollama → Groq → OpenRouter → Mistral).
      2. Re-analisar itens de baixa confiança (< 60%) quando a fila primária
         está vazia — tarefa de utilidade para qualidade contínua.

    Integra:
      - Cascata de provedores de IA com circuit breaker e fallback automático.
      - Detecção de shutdown via shutdown_event para parada graceful.
      - CycleResult completo para telemetria via RewardEngine.
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
            
            # --- TAREFA DE UTILIDADE (PASA v85.12) ---
            # Se não houver novos dados, aproveita o ciclo para RE-ANALISAR itens de baixa confiança (< 60%)
            utility_count = 0
            if classified_count == 0:
                logger.info(f"🧠 [AI] Fila primária vazia. Iniciando Re-análise de Baixa Confiança...")
                utility_count = await ai_service.run_batch_reanalysis(limit=self.batch_size // 2, confidence_threshold=0.6)
                if utility_count > 0:
                    logger.info(f"✨ [AI] Sucesso: {utility_count} registros de baixa confiança refinados.")
            
            if classified_count == 0 and utility_count == 0:
                logger.info("✅ Sem tarefas ou registros para refinar no momento.")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle,
                    target="backlog_ia", source="ai_processor", extracted=0, simulated=False, 
                    error="no_tasks_available", duration=asyncio.get_event_loop().time() - start_time
                )

            total_processed = classified_count + utility_count
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target="backlog_ia", source="ai_processor",
                extracted=total_processed, 
                inserted=0,
                duplicated=0,
                classified=total_processed,
                db_success=True,
                classifier_success=True,
                simulated=False,
                duration=asyncio.get_event_loop().time() - start_time,
                metadata={"utility_tasks": utility_count}
            )

        except Exception as e:
            logger.error(f"💥 Erro no AIProcessorWorker: {e}")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )
