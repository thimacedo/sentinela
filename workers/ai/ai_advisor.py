import logging
from typing import Dict, Any
from workers.base.memory_store import MemoryStore
from workers.ai.doc_fetcher import DocFetcher

class AIAdvisor:
    """
    Advisor que analisa métricas de workers e gera sugestões
    utilizando cache de documentos e (opcionalmente) IA.
    """
    def __init__(self, memory: MemoryStore, fetcher: DocFetcher):
        self.memory = memory
        self.fetcher = fetcher
        self.logger = logging.getLogger("AIAdvisor")

    async def analyze_and_suggest(self, worker, metrics) -> None:
        """Analisa a situação e salva uma sugestão no banco."""
        # Logica de IA (simulada/integrada com Groq/Gemini)
        doc = self.fetcher.get_relevant(worker.worker_id)
        
        suggestion = f"Análise automatizada para {worker.worker_id}: performance abaixo do esperado."
        if doc:
            suggestion += " Baseado na documentação de API, verifique limites de rate."

        await self.memory.save_suggestion(
            worker_id=worker.worker_id,
            cycle=metrics.cycle,
            suggestion=suggestion
        )
        self.logger.info(f"Sugestão salva para {worker.worker_id}")
