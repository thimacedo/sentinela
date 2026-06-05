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
    Reclassifica amostras de alta confiança utilizando provedores independentes (Groq/Llama)
    para detectar desvios de calibragem (drift) na classificação de produção.
    PASA v88.2 (Refatorado para BaseSubAgent e Cascata de IA com Circuit Breaker)
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

    async def setup(self) -> None:
        await super().setup()

    async def teardown(self) -> None:
        await super().teardown()

    async def run_cycle(self):
        # Cumpre o contrato do BaseWorker executando a auditoria com os padrões do sistema
        return await self.run_audit()

    async def run_audit(
        self, 
        sample_size: int = 10, 
        confidence_threshold: float = 0.85, 
        drift_alert_threshold: float = 20.0
    ) -> Dict[str, Any]:
        """
        Executa um ciclo completo de auditoria cruzada analítica.
        """
        # Garante setup se necessário
        is_self_setup = False
        if not self._cpu_executor:
            await self.setup()
            is_self_setup = True

        logger.info(f"[{self.worker_id}] Iniciando ciclo de auditoria (amostra={sample_size}, confianca>={confidence_threshold:.0%})")

        try:
            # 1. Busca amostra de alta confiança via DatabaseAgent local
            sample = await self._fetch_sample(confidence_threshold, sample_size)
            if not sample:
                logger.info(f"[{self.worker_id}] Dados insuficientes para auditoria neste ciclo.")
                return {"success": True, "checked": 0, "discrepancies": 0, "drift_rate": 0.0, "message": "no_tasks_available"}

            # 2. Executa a auditoria cruzada reclassificando amostras
            discrepancies, checked = await self._run_audit_loop(sample)
            drift_rate = (discrepancies / checked * 100) if checked > 0 else 0.0

            logger.info(f"[{self.worker_id}] Concluido | Auditados={checked} | Divergencias={discrepancies} | Drift={drift_rate:.1f}%")

            # --- Fase 3: Cria sugestão de prioridade HIGH se o drift ultrapassar o limiar ---
            drift_alert = drift_rate > drift_alert_threshold
            if drift_alert:
                logger.warning(f"[{self.worker_id}] ALERTA: Taxa de drift {drift_rate:.1f}% supera limiar de {drift_alert_threshold:.1f}%.")
                try:
                    sugestao_txt = f"drift_detected: taxa de drift de {drift_rate:.1f}% supera o limiar de {drift_alert_threshold:.1f}% na calibragem MCA v2.2. Recomenda-se revisao das regras de classificacao e calibragem do modelo de producao. | Prioridade: HIGH"
                    db.client.table("worker_suggestions").insert({
                        "worker_id": self.worker_id,
                        "cycle": self.cycle,
                        "suggestion": sugestao_txt,
                        "status": "pending_review",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }).execute()
                    logger.info(f"[{self.worker_id}] Sugestao de drift_detected salva com sucesso na tabela worker_suggestions.")
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Falha ao salvar sugestao de drift na tabela worker_suggestions: {e}")

            return {
                "success": True,
                "checked": checked,
                "discrepancies": discrepancies,
                "drift_rate_pct": round(drift_rate, 2),
                "drift_alert": drift_alert
            }
        finally:
            if is_self_setup:
                await self.teardown()

    async def _fetch_sample(self, confidence_threshold: float, sample_size: int) -> List[Dict[str, Any]]:
        """Busca amostras de alta confiança consumindo o DatabaseAgent local."""
        sql = f"""
            SELECT id, texto_limpo, categoria_ia, is_hate 
            FROM comentarios 
            WHERE confianca_ia >= {confidence_threshold} 
              AND categoria_ia IS NOT NULL 
              AND categoria_ia != 'ERRO'
            LIMIT 100
        """
        pool = await self.db_agent.query(sql)
        if not pool:
            return []

        if len(pool) < sample_size:
            logger.info(f"[{self.worker_id}] Pool de amostras insuficiente ({len(pool)} < {sample_size}). Usando pool completo.")
            return pool

        return random.sample(pool, sample_size)

    async def _run_audit_loop(self, sample: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Itera reclassificando e marcando divergências."""
        discrepancies = 0
        checked = 0

        async with httpx.AsyncClient(timeout=15.0) as client:
            for comment in sample:
                result = await self._classify_with_cascade(client, comment)
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

    async def _classify_with_cascade(self, client: httpx.AsyncClient, comment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Classifica uma amostra respeitando a cascata resiliente e o Circuit Breaker."""
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

        providers_to_try = ["groq", "mistral", "ollama"]

        for prov in providers_to_try:
            if not ai_circuit_breaker.can_execute(prov):
                logger.warning(f"[{self.worker_id}] Circuito ABERTO para {prov}. Pulando provedor na cascata...")
                continue

            try:
                if prov == "groq" and self._groq_api_key:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
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
                    ai_circuit_breaker.record_success("groq")
                    return json.loads(raw)

                elif prov == "mistral" and os.getenv("MISTRAL_API_KEY"):
                    resp = await client.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"},
                        json={
                            "model": "open-mistral-nemo",
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.1,
                        },
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    raw = resp.json()["choices"][0]["message"]["content"]
                    ai_circuit_breaker.record_success("mistral")
                    return json.loads(raw)

                elif prov == "ollama":
                    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1") + "/chat/completions"
                    resp = await client.post(
                        ollama_url,
                        json={
                            "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b"),
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.1,
                        },
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    raw = resp.json()["choices"][0]["message"]["content"]
                    ai_circuit_breaker.record_success("ollama")
                    return json.loads(raw)

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                logger.warning(f"[{self.worker_id}] Falha no provedor {prov} (HTTP {status_code})")
                ai_circuit_breaker.record_failure(prov, status_code)
                if status_code == 429:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"[{self.worker_id}] Falha inesperada no provedor {prov}: {e}")
                ai_circuit_breaker.record_failure(prov, 500)

        logger.error(f"[{self.worker_id}] Todos os provedores de auditoria falharam ou estao sob Circuit Breaker.")
        return None

    async def _mark_discrepancy(self, comment_id: str, result: Dict[str, Any]) -> None:
        """Marca o comentário divergente no banco Supabase remoto."""
        try:
            db.client.table("comentarios").update({
                "needs_review": True,
                "audit_discrepancy": True,
                "audit_data": result,
            }).eq("id", comment_id).execute()
            logger.debug(f"[{self.worker_id}] Divergencia marcada para ID {comment_id}")
        except Exception as e:
            logger.warning(f"[{self.worker_id}] Falha ao atualizar discrepancia no DB para ID {comment_id}: {e}")
