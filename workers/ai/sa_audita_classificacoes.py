from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timezone
import httpx
from typing import List, Dict, Any, Optional, Tuple

from core.db import db_client as db
from core.circuit_breaker import ai_circuit_breaker
from workers.base.subagent_base import BaseSubAgent
from workers.ai.sa_consulta_banco import SaConsultaBanco

logger = logging.getLogger("SaAuditaClassificacoes")

class SaAuditaClassificacoes(BaseSubAgent):
    """
    Subagente de auditoria analítica e verificação cruzada anti-alucinação.
    PASA v92.7 (Refatorado para BaseSubAgent, MCA v2.2 e Proteção SQL)
    """
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama-3.3-70b-versatile"

    VALID_CATEGORIES = {
        "ODIO_IDENTITARIO", "VIOLENCIA_GENERO", "AMEACA",
        "ATAQUE_INSTITUCIONAL", "RIGOR_CRIMINAL", "INSULTO_AD_HOMINEM", "NEUTRO",
    }

    def __init__(
        self, 
        database_agent: Optional[SaConsultaBanco] = None, 
        worker_id: str = "sa-audita-classificacoes-01", 
        config: Optional[dict] = None
    ):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.db_agent = database_agent or SaConsultaBanco()
        self._groq_api_key = os.getenv("GROQ_API_KEY")

    def describe(self) -> str:
        return "SaAuditaClassificacoes — Auditoria cruzada de modelos e detecção de drift analítico"

    async def run_cycle(self) -> CycleResult:
        # Cumpre o contrato do BaseSubAgent
        audit_res = await self.run_audit()
        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            status="success" if audit_res.get("success") else "failed",
            extracted=audit_res.get("checked", 0),
            classified=audit_res.get("checked", 0),
            db_success=True,
            source="sa_audita_classificacoes",
            metadata=audit_res
        )

    async def run_audit(
        self, 
        sample_size: int = 10, 
        confidence_threshold: float = 0.85, 
        drift_alert_threshold: float = 20.0
    ) -> Dict[str, Any]:
        """Executa um ciclo completo de auditoria cruzada analítica."""
        logger.info(f"[{self.worker_id}] Iniciando ciclo de auditoria (amostra={sample_size}, confianca>={confidence_threshold:.0%})")

        try:
            # 1. Busca amostra via DatabaseAgent local
            sample = await self._fetch_sample(confidence_threshold, sample_size)
            if not sample:
                return {"success": True, "checked": 0, "discrepancies": 0, "message": "no_tasks_available"}

            # 2. Executa a auditoria cruzada
            discrepancies, checked = await self._run_audit_loop(sample)
            drift_rate = (discrepancies / checked * 100) if checked > 0 else 0.0

            # 3. Alerta de Drift
            drift_alert = drift_rate > drift_alert_threshold
            if drift_alert:
                await self._report_drift(drift_rate, drift_alert_threshold)

            return {
                "success": True,
                "checked": checked,
                "discrepancies": discrepancies,
                "drift_rate_pct": round(drift_rate, 2),
                "drift_alert": drift_alert
            }
        except Exception as e:
            logger.error(f"Erro na auditoria: {e}")
            return {"success": False, "error": str(e)}

    async def _fetch_sample(self, confidence_threshold: float, sample_size: int) -> List[Dict[str, Any]]:
        # Sanitização de tipos para evitar injeção
        try:
            conf = float(confidence_threshold)
        except ValueError:
            conf = 0.85

        sql = f"""
            SELECT id, texto_limpo, categoria_ia
            FROM comentarios 
            WHERE confianca_ia >= {conf} 
              AND categoria_ia IS NOT NULL 
              AND categoria_ia != 'ERRO'
            LIMIT 100
        """
        pool = await self.db_agent.query(sql)
        if not pool: return []
        if len(pool) < sample_size: return pool
        return random.sample(pool, sample_size)

    async def _run_audit_loop(self, sample: List[Dict[str, Any]]) -> Tuple[int, int]:
        discrepancies = 0
        checked = 0
        from core.constants import HATE_CATEGORIES

        async with httpx.AsyncClient(timeout=15.0) as client:
            for comment in sample:
                result = await self._classify_with_cascade(client, comment)
                if result is None: continue

                checked += 1
                orig_cat = comment.get("categoria_ia")
                groq_cat = result.get("categoria_ia", "NEUTRO")
                
                orig_is_hate = orig_cat in HATE_CATEGORIES
                groq_is_hate = groq_cat in HATE_CATEGORIES

                if groq_cat != orig_cat or groq_is_hate != orig_is_hate:
                    discrepancies += 1
                    await self._mark_discrepancy(comment["id"], result)

        return discrepancies, checked

    async def _classify_with_cascade(self, client: httpx.AsyncClient, comment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        texto = (comment.get("texto_limpo") or "").strip()
        if not texto: return None

        categorias_str = ", ".join(sorted(self.VALID_CATEGORIES))
        prompt = (
            f"Auditoria de IA - Taxonomia MCA v2.2.\n"
            f"Categorias: {categorias_str}.\n"
            f'JSON: {{"rotulo": "hate" ou "not_hate", "categoria_ia": "CATEGORIA"}}\n'
            f'Texto: "{texto}"'
        )

        for prov in ["groq", "mistral", "ollama"]:
            if not ai_circuit_breaker.can_execute(prov): continue
            try:
                if prov == "groq" and self._groq_api_key:
                    resp = await client.post(self.GROQ_URL, headers={"Authorization": f"Bearer {self._groq_api_key}"},
                        json={"model": self.GROQ_MODEL, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}, "temperature": 0.1},
                        timeout=10.0)
                    resp.raise_for_status()
                    ai_circuit_breaker.record_success("groq")
                    return json.loads(resp.json()["choices"][0]["message"]["content"])
                # ... outros provedores omitidos para brevidade, mas seguem a mesma lógica
            except Exception as e:
                logger.warning(f"Falha no provedor {prov}: {e}")
                ai_circuit_breaker.record_failure(prov, 500)
        return None

    async def _report_drift(self, rate: float, threshold: float):
        try:
            sugestao = f"drift_detected: {rate:.1f}% > {threshold:.1f}% na calibragem MCA v2.2. Recomenda-se revisao."
            await asyncio.to_thread(db.client.table("worker_suggestions").insert({
                "worker_id": self.worker_id, "cycle": self.cycle, "suggestion": sugestao, "status": "pending_review",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }).execute)
        except Exception as e: logger.error(f"Erro ao reportar drift: {e}")

    async def _mark_discrepancy(self, comment_id: str, result: Dict[str, Any]) -> None:
        try:
            await asyncio.to_thread(db.client.table("comentarios").update({
                "needs_review": True, "audit_discrepancy": True, "audit_data": result
            }).eq("id", comment_id).execute)
        except Exception as e: logger.warning(f"Erro ao marcar discrepancia: {e}")
