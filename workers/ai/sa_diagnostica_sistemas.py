import logging
import json
import os
from typing import Dict, Any
from workers.base.memory_store import MemoryStore
from workers.ai.doc_fetcher import DocFetcher
from core.ai_service import AIService

class SaDiagnosticaSistemas:
    """
    Advisor que analisa métricas de workers e gera sugestões
    utilizando cache de documentos e IA Cloud (Mistral/Groq).
    """
    def __init__(self, memory: MemoryStore, fetcher: DocFetcher):
        self.memory = memory
        self.fetcher = fetcher
        self.logger = logging.getLogger("SaDiagnosticaSistemas")
        self.ai_service = AIService() # Reutiliza infra de cascata

    async def analyze_and_suggest(self, worker, result) -> None:
        """Analisa a situação degradada e salva uma sugestão no banco."""
        doc = self.fetcher.get_relevant(worker.worker_id)
        
        # Build context for AI
        metrics_summary = {
            "worker_id": result.worker_id,
            "cycle": result.cycle,
            "target": result.target,
            "extracted": result.extracted,
            "failed": result.failed,
            "error": result.error,
            "duration": result.metadata.get("duration_seconds", 0),
            "db_success": result.db_success
        }

        system_prompt = (
            "Você é o Sentinela SRE Advisor. Sua missão é analisar falhas em workers de coleta de dados (Instagram).\n"
            "Analise as métricas e a documentação técnica fornecida e sugira uma ação corretiva específica.\n"
            "Responda em Português Brasileiro, de forma técnica e concisa.\n"
            "Formato de resposta: 'ANÁLISE: ... SUGESTÃO: ...'"
        )

        user_content = f"METRICAS: {json.dumps(metrics_summary)}\n"
        if doc:
            user_content += f"\nDOCUMENTAÇÃO TÉCNICA:\n{doc}\n"

        try:
            # Usamos o classify_text mas com um prompt customizado (overshadowing o default via injeção se possível, 
            # ou chamando o client do AIService diretamente para flexibilidade)
            # Para manter o padrão de cascata do AIService, vamos injetar o prompt no user_content
            
            response = await self.ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                timeout=20.0
            )
            suggestion = response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"Erro ao consultar IA para Advisor: {e}")
            suggestion = f"Falha crítica no ciclo {result.cycle}. Erro reportado: {result.error}. Verifique logs de rede."

        await self.memory.save_suggestion(
            worker_id=result.worker_id,
            cycle=result.cycle,
            suggestion=suggestion
        )
        self.logger.info(f"💡 [SaDiagnosticaSistemas] Sugestão salva para {result.worker_id}: {suggestion[:50]}...")
