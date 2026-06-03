"""
PASA v88.0 — AuditWorker: Sub-agente de Verificação Cruzada Anti-Alucinação
Reclassifica amostras de alta confiança via Groq (Llama 3) para detectar divergências (drift).
Migrado de script standalone para BaseWorker com ciclo de vida gerenciado.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from typing import Optional

import httpx

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.db import db_client as db

logger = logging.getLogger("worker.audit")


class AuditWorker(BaseWorker):
    """
    Sub-agente de auditoria cruzada.

    Ciclo:
      1. Busca N comentários de alta confiança (≥ 85%) já classificados.
      2. Reclassifica cada um via Groq (Llama 3.3-70B) — provedor independente.
      3. Compara com a classificação original e marca divergências no banco.
      4. Alerta via log se a taxa de drift ultrapassar o limiar configurado.

    Critério de saúde: drift_rate < drift_alert_threshold (padrão 20%).
    """

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama-3.3-70b-versatile"

    # Categorias válidas pelo MCA v2.2
    VALID_CATEGORIES = {
        "ODIO_IDENTITARIO", "VIOLENCIA_GENERO", "AMEACA",
        "ATAQUE_INSTITUCIONAL", "RIGOR_CRIMINAL", "INSULTO_AD_HOMINEM", "NEUTRO",
    }

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.sample_size: int = config.get("sample_size", 10)
        self.confidence_threshold: float = config.get("confidence_threshold", 0.85)
        self.drift_alert_threshold: float = config.get("drift_alert_threshold", 20.0)
        self._groq_api_key: Optional[str] = None

    def describe(self) -> str:
        return (
            f"AuditWorker — Auditoria Cruzada Anti-Alucinação "
            f"(n={self.sample_size}, confiança≥{self.confidence_threshold:.0%}, "
            f"drift_alerta={self.drift_alert_threshold:.0f}%)"
        )

    async def setup(self) -> None:
        self._groq_api_key = os.getenv("GROQ_API_KEY")
        if not self._groq_api_key:
            logger.error("🛑 [AuditWorker] GROQ_API_KEY não configurada. Auditoria desabilitada.")
        else:
            logger.info("✅ [AuditWorker] Inicializado. %s", self.describe())

    async def teardown(self) -> None:
        logger.info("🛑 [AuditWorker] Encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        # Verifica shutdown antes de começar
        if self.shutdown_event and self.shutdown_event.is_set():
            logger.info("🛑 [AuditWorker] Shutdown detectado. Abortando ciclo %d.", self.cycle)
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="audit",
                error="shutdown_requested",
                duration=asyncio.get_event_loop().time() - start_time,
            )

        if not self._groq_api_key:
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="audit",
                error="groq_api_key_missing",
                duration=asyncio.get_event_loop().time() - start_time,
            )

        logger.info("🔍 [AuditWorker] Ciclo #%d iniciado (n=%d).", self.cycle, self.sample_size)

        # 1. Busca amostra de comentários de alta confiança
        sample = await self._fetch_sample()
        if not sample:
            logger.info("✅ [AuditWorker] Dados insuficientes para auditoria neste ciclo.")
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="audit",
                error="no_tasks_available",
                duration=asyncio.get_event_loop().time() - start_time,
            )

        # 2. Reclassifica via Groq e computa divergências
        discrepancies, checked = await self._run_audit(sample)
        drift_rate = (discrepancies / checked * 100) if checked > 0 else 0.0

        logger.info(
            "📊 [AuditWorker] Ciclo #%d | Auditados=%d | Divergências=%d | Drift=%.1f%%",
            self.cycle, checked, discrepancies, drift_rate,
        )

        if drift_rate > self.drift_alert_threshold:
            logger.warning(
                "🚨 [AuditWorker] ALERTA: Taxa de drift %.1f%% supera limiar de %.1f%%. "
                "Verificar provedor de IA principal.",
                drift_rate, self.drift_alert_threshold,
            )

        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            source="audit",
            audit_checked=checked,
            extracted=checked,
            failed=discrepancies,
            db_success=True,
            simulated=False,
            duration=asyncio.get_event_loop().time() - start_time,
            metadata={
                "discrepancies": discrepancies,
                "drift_rate_pct": round(drift_rate, 2),
                "drift_alert": drift_rate > self.drift_alert_threshold,
            },
        )

    # ── Métodos privados ──────────────────────────────────────────────────────

    async def _fetch_sample(self) -> list[dict]:
        """Busca comentários de alta confiança para auditar."""
        try:
            # Tenta coluna 'confianca_ia' (schema atual)
            res = (
                db.client.table("comentarios")
                .select("id, texto_limpo, categoria_ia, is_hate")
                .gte("confianca_ia", self.confidence_threshold)
                .eq("processado_ia", True)
                .limit(100)
                .execute()
            )
        except Exception:
            # Fallback para schema legado 'confianza_ia'
            try:
                res = (
                    db.client.table("comentarios")
                    .select("id, texto_limpo, categoria_ia, is_hate")
                    .gte("confianza_ia", self.confidence_threshold)
                    .eq("processado_ia", True)
                    .limit(100)
                    .execute()
                )
            except Exception as e:
                logger.error("❌ [AuditWorker] Erro ao buscar amostra: %s", e)
                return []

        pool = res.data or []
        if len(pool) < self.sample_size:
            logger.info(
                "⚠️ [AuditWorker] Pool insuficiente (%d < %d). Usando pool completo.",
                len(pool), self.sample_size,
            )
            return pool

        return random.sample(pool, self.sample_size)

    async def _run_audit(self, sample: list[dict]) -> tuple[int, int]:
        """
        Reclassifica via Groq e marca divergências no banco.
        Retorna (discrepâncias, total_auditado).
        """
        discrepancies = 0
        checked = 0

        async with httpx.AsyncClient(timeout=15.0) as client:
            for comment in sample:
                if self.shutdown_event and self.shutdown_event.is_set():
                    logger.info("🛑 [AuditWorker] Shutdown durante auditoria. Parando.")
                    break

                result = await self._classify_with_groq(client, comment)
                if result is None:
                    continue

                checked += 1
                orig_rotulo = "hate" if comment.get("is_hate") else "not_hate"
                groq_rotulo = result.get("rotulo", "not_hate")
                groq_categoria = result.get("categoria_ia", "NEUTRO")

                divergiu = (
                    groq_categoria != comment.get("categoria_ia")
                    or groq_rotulo != orig_rotulo
                )

                if divergiu:
                    discrepancies += 1
                    await self._mark_discrepancy(comment["id"], result)

        return discrepancies, checked

    async def _classify_with_groq(
        self, client: httpx.AsyncClient, comment: dict
    ) -> dict | None:
        """Classifica um comentário via Groq e retorna o resultado parseado."""
        texto = (comment.get("texto_limpo") or "").strip()
        if not texto:
            return None

        categorias_str = ", ".join(sorted(self.VALID_CATEGORIES))
        prompt = (
            f"Você é um auditor de inteligência artificial. "
            f"Classifique o texto a seguir seguindo a Taxonomia MCA v2.2.\n"
            f"Categorias válidas: {categorias_str}.\n"
            f'Responda APENAS com JSON válido: {{"rotulo": "hate" ou "not_hate", "categoria_ia": "CATEGORIA"}}\n'
            f'Regras: is_hate=hate apenas para AMEACA, ODIO_IDENTITARIO, VIOLENCIA_GENERO.\n'
            f'Texto: "{texto}"'
        )

        try:
            resp = await client.post(
                self.GROQ_URL,
                headers={"Authorization": f"Bearer {self._groq_api_key}"},
                json={
                    "model": self.GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            return json.loads(raw)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("⏳ [AuditWorker] Rate limit Groq. Aguardando 5s...")
                await asyncio.sleep(5)
            else:
                logger.error("❌ [AuditWorker] HTTP %d na auditoria de ID %s", e.response.status_code, comment["id"])
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("⚠️ [AuditWorker] JSON inválido do Groq para ID %s: %s", comment["id"], e)
            return None
        except Exception as e:
            logger.error("❌ [AuditWorker] Erro inesperado para ID %s: %s", comment["id"], e)
            return None

    async def _mark_discrepancy(self, comment_id: str, groq_result: dict) -> None:
        """Marca o comentário como divergente no banco para revisão humana."""
        try:
            db.client.table("comentarios").update({
                "needs_review": True,
                "audit_discrepancy": True,
                "audit_data": groq_result,
            }).eq("id", comment_id).execute()
            logger.debug("🔖 [AuditWorker] Divergência registrada para ID %s.", comment_id)
        except Exception as e:
            logger.warning(
                "⚠️ [AuditWorker] Falha ao marcar divergência no DB para ID %s: %s",
                comment_id, e,
            )
