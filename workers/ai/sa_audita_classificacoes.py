import asyncio
import json
import logging
import os
import random
import httpx
from typing import List, Dict, Any, Optional, Tuple
from core.db import db_client as db
from workers.ai.sa_consulta_banco import SaConsultaBanco

logger = logging.getLogger("SaAuditaClassificacoes")

class SaAuditaClassificacoes:
    """
    Subagente de auditoria analítica e verificação cruzada anti-alucinação.
    Reclassifica amostras de alta confiança utilizando provedores independentes (Groq/Llama)
    para detectar desvios de calibragem (drift) na classificação de produção.
    """
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama-3.3-70b-versatile"

    VALID_CATEGORIES = {
        "ODIO_IDENTITARIO", "VIOLENCIA_GENERO", "AMEACA",
        "ATAQUE_INSTITUCIONAL", "RIGOR_CRIMINAL", "INSULTO_AD_HOMINEM", "NEUTRO",
    }

    def __init__(self, database_agent: Optional[SaConsultaBanco] = None):
        self.db_agent = database_agent or SaConsultaBanco()
        self._groq_api_key = os.getenv("GROQ_API_KEY")

    async def run_audit(
        self, 
        sample_size: int = 10, 
        confidence_threshold: float = 0.85, 
        drift_alert_threshold: float = 20.0
    ) -> Dict[str, Any]:
        """
        Executa um ciclo completo de auditoria cruzada analítica.
        """
        if not self._groq_api_key:
            logger.error("[SaAuditaClassificacoes] GROQ_API_KEY nao configurada. Auditoria abortada.")
            return {"success": False, "error": "groq_api_key_missing"}

        logger.info(f"[SaAuditaClassificacoes] Iniciando ciclo de auditoria (amostra={sample_size}, confianca>={confidence_threshold:.0%})")

        # 1. Busca amostra de alta confiança via DatabaseAgent local (porta 8002)
        sample = await self._fetch_sample(confidence_threshold, sample_size)
        if not sample:
            logger.info("[SaAuditaClassificacoes] Dados insuficientes para auditoria neste ciclo.")
            return {"success": True, "checked": 0, "discrepancies": 0, "drift_rate": 0.0, "message": "no_tasks_available"}

        # 2. Executa a auditoria cruzada reclassificando amostras
        discrepancies, checked = await self._run_audit_loop(sample)
        drift_rate = (discrepancies / checked * 100) if checked > 0 else 0.0

        logger.info(f"[SaAuditaClassificacoes] Concluido | Auditados={checked} | Divergencias={discrepancies} | Drift={drift_rate:.1f}%")

        if drift_rate > drift_alert_threshold:
            logger.warning(f"[SaAuditaClassificacoes] ALERTA: Taxa de drift {drift_rate:.1f}% supera limiar de {drift_alert_threshold:.1f}%.")

        return {
            "success": True,
            "checked": checked,
            "discrepancies": discrepancies,
            "drift_rate_pct": round(drift_rate, 2),
            "drift_alert": drift_rate > drift_alert_threshold
        }

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
            logger.info(f"[SaAuditaClassificacoes] Pool de amostras insuficiente ({len(pool)} < {sample_size}). Usando pool completo.")
            return pool

        return random.sample(pool, sample_size)

    async def _run_audit_loop(self, sample: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Itera reclassificando e marcando divergências."""
        discrepancies = 0
        checked = 0

        async with httpx.AsyncClient(timeout=15.0) as client:
            for comment in sample:
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

    async def _classify_with_groq(self, client: httpx.AsyncClient, comment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Classifica uma amostra via Groq e retorna o JSON estruturado."""
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
                logger.warning("[SaAuditaClassificacoes] Rate limit Groq na auditoria. Aguardando 5s...")
                await asyncio.sleep(5)
            else:
                logger.error(f"[SaAuditaClassificacoes] HTTP {e.response.status_code} no comentario ID {comment['id']}")
            return None
        except Exception as e:
            logger.error(f"[SaAuditaClassificacoes] Erro na reclassificacao do ID {comment['id']}: {e}")
            return None

    async def _mark_discrepancy(self, comment_id: str, groq_result: Dict[str, Any]) -> None:
        """Marca o comentário divergente no banco Supabase remoto."""
        try:
            db.client.table("comentarios").update({
                "needs_review": True,
                "audit_discrepancy": True,
                "audit_data": groq_result,
            }).eq("id", comment_id).execute()
            logger.debug(f"[SaAuditaClassificacoes] Divergencia marcada para ID {comment_id}")
        except Exception as e:
            logger.warning(f"[SaAuditaClassificacoes] Falha ao atualizar discrepancia no DB para ID {comment_id}: {e}")
