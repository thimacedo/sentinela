from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from core.voyant_service import voyant_service
from core.db import db_client
from core.ai_service import ai_service

logger = logging.getLogger("SaVoyant")

# Caminho da Bíblia Linguística — resolução relativa à raiz do projeto
_BIBLIA_PATH = "bases_pdf/BIBLIA_LINGUISTICA_FORENSE_PASA.md"
_BIBLIA_MAX_CHARS = 2000


class SaVoyant(BaseSubAgent):
    """
    Subagente Linguista (SaVoyant) — PASA v92.4.1
    Integra Voyant Tools com Raciocínio de IA e Bases de Linguística Forense.

    Responsabilidades:
      - Fast-Drop: filtrar lotes neutros (hostile_ratio < threshold) sem acionar LLM.
      - Triagem léxica via TF-IDF (Voyant/Trombone).
      - Identificar padrões de Ataque Institucional e Xenofobia via N-gramas.
      - Gerar insights periciais salvos em system_events.
    """

    def __init__(self, worker_id: str = "sa-voyant-01", config: Optional[dict] = None):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.hostile_threshold = float(os.getenv("VOYANT_HOSTILE_THRESHOLD", "0.08"))
        self._linguistics_context: str = ""  # cache carregado no setup()

    def describe(self) -> str:
        return "SaVoyant — Subagente de Inteligência Linguística e Triagem PLN Determinística."

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    async def setup(self) -> None:
        await super().setup()

        # Verifica VoyantServer
        if not await voyant_service.ping():
            logger.warning(
                "⚠️ [%s] VoyantServer offline. Operando em modo degradado (apenas IA).",
                self.worker_id,
            )

        # Carrega Bíblia Linguística uma vez, em thread, para não bloquear o event loop
        self._linguistics_context = await asyncio.to_thread(self._load_biblia)
        if self._linguistics_context:
            logger.info("📖 [%s] Bíblia Linguística carregada (%d chars).", self.worker_id, len(self._linguistics_context))
        else:
            logger.warning("⚠️ [%s] Bíblia Linguística não encontrada em '%s'. Insights terão contexto reduzido.", self.worker_id, _BIBLIA_PATH)

    async def teardown(self) -> None:
        await super().teardown()

    # ── Ciclo principal ──────────────────────────────────────────────────────

    async def run_cycle(self) -> CycleResult:
        """Executa a análise linguística pericial do lote atual."""
        self.cycle += 1  # FIX: incremento obrigatório para métricas corretas

        try:
            # 1. Puxa comentários recentes
            res = await asyncio.to_thread(
                db_client.client.table("comentarios")
                .select("*")
                .order("data_coleta", desc=True)
                .limit(100)
                .execute
            )
            comments = res.data or []

            if not comments:
                return self._idle_result("Sem comentários para análise linguística.")

            # FIX: filtra None antes de enviar ao Voyant
            texts = [
                c.get("texto_limpo") or c.get("texto_bruto")
                for c in comments
                if c.get("texto_limpo") or c.get("texto_bruto")
            ]

            if not texts:
                return self._idle_result("Todos os comentários estão sem texto utilizável.")

            # 2. Análise determinística via VoyantService
            voyant_data = await voyant_service.triage_batch(texts)

            # 3. Fast-Drop: lote neutro → zero custo cloud
            if voyant_data and voyant_data.get("hostile_ratio", 0) < self.hostile_threshold:
                logger.info(
                    "🟢 [%s] Fast-Drop ativado: hostile_ratio=%.2f%% < threshold=%.0f%%. "
                    "Lote classificado como NEUTRO sem acionar LLM.",
                    self.worker_id,
                    voyant_data["hostile_ratio"] * 100,
                    self.hostile_threshold * 100,
                )
                return CycleResult(
                    worker_id=self.worker_id,
                    cycle=self.cycle,
                    source="sa_voyant",
                    extracted=len(comments),
                    classified=len(comments),
                    db_success=True,
                    simulated=False,
                    metadata={
                        "xp_delta": 5.0,
                        "fast_drop": True,
                        "hostile_ratio": voyant_data["hostile_ratio"],
                        "top_terms": list(voyant_data.get("top_terms", {}).keys())[:10],
                        "insight_title": None,
                    },
                )

            # 4. Raciocínio de IA sobre dados do Voyant + Bíblia Linguística
            insight = await self._generate_linguistic_insight(voyant_data)

            # 5. Persistência do insight se relevante
            if insight and insight.get("relevancia", 0) > 0.6:
                await self._save_insight(insight)
                logger.info("✅ [%s] Insight Linguístico gerado: %s", self.worker_id, insight.get("titulo"))

            xp = 15.0 if (insight and insight.get("relevancia", 0) > 0.8) else 5.0

            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="sa_voyant",
                extracted=len(comments),
                classified=len(comments) if voyant_data else 0,
                db_success=True,
                simulated=False,
                metadata={
                    "xp_delta": xp,  # FIX: RewardEngine usa este campo para XP manual
                    "hostile_ratio": voyant_data.get("hostile_ratio", 0) if voyant_data else 0,
                    "top_terms": list(voyant_data.get("top_terms", {}).keys())[:10] if voyant_data else [],
                    "insight_title": insight.get("titulo") if insight else None,
                },
            )

        except Exception as e:
            logger.error("💥 [%s] Erro no ciclo Voyant: %s", self.worker_id, e, exc_info=True)
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="sa_voyant",
                error=str(e)[:200],
            )

    # ── Lógica interna ───────────────────────────────────────────────────────

    def _load_biblia(self) -> str:
        """Lê a Bíblia Linguística do disco (síncrono — deve ser chamado via to_thread)."""
        try:
            with open(_BIBLIA_PATH, "r", encoding="utf-8") as f:
                return f.read()[:_BIBLIA_MAX_CHARS]
        except FileNotFoundError:
            return ""
        except Exception as e:
            logger.error("❌ [%s] Erro ao carregar Bíblia Linguística: %s", self.worker_id, e)
            return ""

    async def _generate_linguistic_insight(self, voyant_data: Optional[dict]) -> Optional[dict]:
        """Usa IA para cruzar dados do Voyant com a Bíblia Linguística."""
        if not voyant_data:
            return None

        prompt = f"""
Analise os seguintes dados léxicos extraídos pelo Voyant Tools de um lote de redes sociais:

DADOS VOYANT:
- Ratio Hostil: {voyant_data.get('hostile_ratio', 0):.2%}
- Termos Hostis Detectados: {voyant_data.get('hostile_terms', [])}
- Top Vocabulário: {list(voyant_data.get('top_terms', {}).keys())[:20]}

BASE LINGUÍSTICA (REGRAS):
{self._linguistics_context}

TAREFA:
1. Identifique se há um padrão de 'Xenofobia Regionalizada', 'Ataque Institucional' ou 'Sarcasmo'.
2. Avalie a severidade real do lote (0-100).
3. Gere um título curto e um resumo pericial.

RETORNE APENAS JSON:
{{
    "titulo": "Título do Insight",
    "resumo": "Análise detalhada...",
    "relevancia": 0.0,
    "severidade": 0,
    "categoria_mca": "EX: ODIO_IDENTITARIO"
}}
"""
        try:
            return await ai_service.chat_completion(
                prompt=prompt,
                system_prompt="Você é o Subagente Voyant, especialista em Linguística Forense Política.",
                response_format="json_object",
            )
        except Exception as e:
            logger.warning("⚠️ [%s] Falha ao gerar insight linguístico: %s", self.worker_id, e)
            return None

    async def _save_insight(self, insight: dict) -> None:
        """Salva o insight no banco como evento de sistema."""
        try:
            await asyncio.to_thread(
                db_client.client.table("system_events").insert({
                    "event_type": "linguistic_insight",
                    "source": self.worker_id,
                    "severity": "warning" if insight.get("severidade", 0) > 50 else "info",
                    "description": f"{insight.get('titulo', 'Insight')}: {insight.get('resumo', '')}",
                    "metadata": insight,
                }).execute
            )
        except Exception as e:
            logger.error("❌ [%s] Erro ao salvar insight: %s", self.worker_id, e)

    # ── Helpers de resultado ─────────────────────────────────────────────────

    def _idle_result(self, msg: str) -> CycleResult:
        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            source="sa_voyant",
            error="no_tasks_available",  # FIX: string padrão reconhecida pelo orchestrator
            metadata={"reason": msg},
        )
