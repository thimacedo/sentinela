"""
SaFastDrop — Pré-triagem Léxica Local (PASA v51.0)
═══════════════════════════════════════════════════
Substitui o SaVoyant sem nenhuma dependência externa.
- Zero Java (sem VoyantServer)
- Zero HTTP externo
- Zero chamadas LLM

Usa exclusivamente core/lexical_filter.py (Python puro).

Lógica:
  - Lote de comentários não processados (processado_ia=False)
  - Se is_junk() → descarta (LIXO, não entra na fila de IA)
  - Se should_shadowban() → registra como SPAM, não exibe no dashboard
  - O restante vai para o WkClassificaComentarios com LLM
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from core.lexical_filter import lexical_filter
from core.db import db_client

logger = logging.getLogger("SaFastDrop")

_BATCH_SIZE = 200  # Comentários por ciclo — leve o suficiente para rodar em < 1s


class SaFastDrop(BaseSubAgent):
    """
    Subagente de Pré-triagem Léxica Local (PASA v51.0).

    Responsabilidade única: descartar lixo e spam ANTES de gastar tokens de LLM.
    NÃO classifica ódio. NÃO toca em candidatos a hostilidade. Apenas descarta
    o que é claramente inútil (emojis soltos, urls, spam de bet, propaganda).
    """

    def __init__(self, worker_id: str = "sa-fast-drop-01", config: Optional[dict] = None):
        super().__init__(worker_id, config or {})
        self._last_processed_id: Optional[str] = None

    def describe(self) -> str:
        return "SaFastDrop — Pré-triagem léxica local. Zero LLM, zero Java."

    async def setup(self) -> None:
        await super().setup()
        logger.info("[%s] Pronto. Usando lexical_filter.py (Python puro).", self.worker_id)

    async def teardown(self) -> None:
        await super().teardown()

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1

        try:
            # Busca lote de não-processados mais antigos
            query = db_client.client.table("comentarios")\
                .select("id, texto_bruto, texto_limpo")\
                .eq("processado_ia", False)\
                .order("data_coleta", desc=False)\
                .limit(_BATCH_SIZE)

            res = await asyncio.to_thread(query.execute)
            comentarios = res.data or []

            if not comentarios:
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle,
                    source="sa_fast_drop", error="no_tasks_available"
                )

            ids_lixo = []
            ids_spam = []

            for c in comentarios:
                texto = c.get("texto_limpo") or c.get("texto_bruto") or ""
                if lexical_filter.is_junk(texto):
                    ids_lixo.append(c["id"])
                elif lexical_filter.should_shadowban(texto):
                    ids_spam.append(c["id"])
                # Comentários que não são lixo nem spam: deixa para o WkClassificaComentarios

            descartados = 0

            # Marca lixo como processado (LIXO — não entra na fila de LLM)
            if ids_lixo:
                await asyncio.to_thread(
                    db_client.client.table("comentarios").update({
                        "processado_ia": True,
                        "categoria_ia": "LIXO",
                        "confianca_ia": 1.0,
                        "analise_pericial": "[SaFastDrop] Descartado por baixa qualidade léxica (lixo)."
                    }).in_("id", ids_lixo).execute
                )
                descartados += len(ids_lixo)
                logger.info("[%s] %d comentários descartados como LIXO.", self.worker_id, len(ids_lixo))

            # Marca spam como processado (SPAM — oculto do dashboard)
            if ids_spam:
                await asyncio.to_thread(
                    db_client.client.table("comentarios").update({
                        "processado_ia": True,
                        "categoria_ia": "NEUTRO",
                        "confianca_ia": 0.90,
                        "analise_pericial": "[SaFastDrop] Shadowban: propaganda/spam detectado."
                    }).in_("id", ids_spam).execute
                )
                descartados += len(ids_spam)
                logger.info("[%s] %d comentários marcados como SPAM (shadowban).", self.worker_id, len(ids_spam))

            uteis = len(comentarios) - descartados
            logger.info(
                "[%s] Ciclo %d | Lote=%d | Descartados=%d | Úteis p/ LLM=%d",
                self.worker_id, self.cycle, len(comentarios), descartados, uteis
            )

            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="sa_fast_drop",
                extracted=len(comentarios),
                classified=descartados,
                db_success=True,
                metadata={"lixo": len(ids_lixo), "spam": len(ids_spam), "uteis_llm": uteis}
            )

        except Exception as e:
            logger.error("[%s] Erro no ciclo: %s", self.worker_id, e, exc_info=True)
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="sa_fast_drop", error=str(e)[:200]
            )
