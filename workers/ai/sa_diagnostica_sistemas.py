from __future__ import annotations
import logging
import json
import os
from typing import Dict, Any, Optional
from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from workers.base.memory_store import MemoryStore
from workers.ai.doc_fetcher import DocFetcher
from core.ai_service import ai_service

class SaDiagnosticaSistemas(BaseSubAgent):
    """
    Advisor que analisa métricas de workers e gera sugestões
    utilizando cache de documentos e a malha de IA unificada (AIService).
    """
    def __init__(
        self, 
        memory: Optional[MemoryStore] = None, 
        fetcher: Optional[DocFetcher] = None,
        worker_id: str = "sa-diagnostica-01",
        config: Optional[dict] = None
    ):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.memory = memory or MemoryStore()
        self.fetcher = fetcher or DocFetcher()

    def describe(self) -> str:
        return "SaDiagnosticaSistemas — Advisor de SRE e Autocura de Workers."

    async def run_cycle(self) -> CycleResult:
        # Este subagente é reativo, acionado pelo orquestrador em caso de falha.
        # Mantemos o run_cycle para compatibilidade com o contrato.
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, status="idle")

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
            response = await ai_service.chat_completion(
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
