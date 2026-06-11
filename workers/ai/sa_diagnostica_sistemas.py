from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from workers.base.memory_store import MemoryStore

logger = logging.getLogger("SaDiagnosticaSistemas")


class SaDiagnosticaSistemas(BaseSubAgent):
    """
    Advisor determinístico que analisa métricas de workers e gera sugestões
    com base em regras locais (PASA v51.0 — zero tokens).
    """

    REGRAS_DIAGNOSTICO = {
        "session": ["session", "login", "cookie", "expired", "auth", "sessao", "sessão"],
        "dom_change": ["selector", "not found", "element", "dom", "seletor"],
        "rate_limit": ["429", "rate limit", "too many", "blocked", "bloqueado"],
        "network": ["timeout", "connection", "refused", "unreachable", "conexão"],
    }

    SUGESTOES_PADRAO = {
        "session": "Sessão expirada detectada. SUGESTÃO: Verificar e renovar cookies do Instagram via script de export.",
        "dom_change": "Seletor DOM falhou. SUGESTÃO: Auditar seletores CSS no instagram_scraper_v2.py e atualizar.",
        "rate_limit": "Rate limit atingido. SUGESTÃO: Aumentar jitter entre requisições e reduzir MAX_POSTS_PER_PROFILE.",
        "network": "Falha de rede detectada. SUGESTÃO: Verificar conectividade e aguardar recuperação automática.",
        "unknown": "Erro desconhecido. SUGESTÃO: Verificar logs detalhados em logs/main_runner.json.",
    }

    def __init__(
        self, 
        memory: Optional[MemoryStore] = None, 
        fetcher: Optional[Any] = None,
        worker_id: str = "sa-diagnostica-01",
        config: Optional[dict] = None
    ):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.memory = memory or MemoryStore()

    def describe(self) -> str:
        return "SaDiagnosticaSistemas — Advisor de SRE e Autocura de Workers (Local)."

    async def run_cycle(self) -> CycleResult:
        # Este subagente é reativo, acionado pelo orquestrador em caso de falha.
        # Mantemos o run_cycle para compatibilidade com o contrato.
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, status="idle")

    async def analyze_and_suggest(self, worker, result) -> None:
        """Analisa a situação degradada e salva uma sugestão no banco."""
        error_text = result.error or ""
        error_lower = error_text.lower()
        
        tipo = "unknown"
        for t, palavras in self.REGRAS_DIAGNOSTICO.items():
            if any(p in error_lower for p in palavras):
                tipo = t
                break
                
        suggestion = self.SUGESTOES_PADRAO[tipo]

        try:
            await self.memory.save_suggestion(
                worker_id=result.worker_id,
                cycle=result.cycle,
                suggestion=suggestion
            )
        except Exception as e:
            logger.error("Erro ao salvar sugestão no banco: %s", e)

        logger.info(
            "💡 [%s] Diagnóstico concluído localmente para %s (tipo=%s). Sugestão persistida.",
            self.worker_id, result.worker_id, tipo
        )

