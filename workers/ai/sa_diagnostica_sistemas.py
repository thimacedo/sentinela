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
    utilizando cache de documentos e a malha de IA unificada (AIService).
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
            "duration": result.metadata.get("duration_seconds", 0) if result.metadata else 0,
            "db_success": result.db_success
        }

        system_prompt = (
            "Você é o Sentinela SRE Advisor. Sua missão é analisar falhas em workers de coleta de dados (Instagram).\n"
            "Analise as métricas e a documentação técnica fornecida e sugira uma ação corretiva específica.\n"
            "Responda em Português Brasileiro, de forma técnica e concisa.\n"
            "Formato de resposta: 'ANÁLISE: ... SUGESTÃO: ...'"
        )

        user_content = f"METRICAS DO CICLO:\n{json.dumps(metrics_summary, indent=2)}\n"
        if doc:
            user_content += f"\nDOCUMENTAÇÃO TÉCNICA DE APOIO:\n{doc}\n"
        else:
            user_content += "\n(Nenhuma documentação técnica específica encontrada para este worker.)\n"

        try:
            # Reutiliza a cascata de IA (Mistral -> Groq -> Ollama) via chat_completion
            # Passamos o system_prompt específico para o Advisor
            response = await self.ai_service.chat_completion(
                prompt=user_content,
                system_prompt=system_prompt,
                response_format="text" # O Advisor retorna texto livre no formato ANÁLISE/SUGESTÃO
            )
            
            if response and "content" in response:
                suggestion = response["content"].strip()
            else:
                suggestion = f"ANÁLISE: Ciclo degradado com erro {result.error}. SUGESTÃO: Verificar conectividade e validade das sessões no .env."

        except Exception as e:
            self.logger.error(f"Erro ao consultar malha de IA para Advisor: {e}")
            suggestion = f"ANÁLISE: Falha crítica no diagnóstico. Erro reportado pelo worker: {result.error}. SUGESTÃO: Reiniciar watchdog e verificar quotas de IA."

        await self.memory.save_suggestion(
            worker_id=result.worker_id,
            cycle=result.cycle,
            suggestion=suggestion
        )
        self.logger.info(f"💡 [SaDiagnosticaSistemas] Diagnóstico concluído para {result.worker_id}. Sugestão persistida.")
