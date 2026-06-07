"""
PASA v92.0 - VoyantService: Motor Determinístico de PLN via Trombone API
=========================================================================
Microserviço de comunicação assíncrona com o backend do VoyantServer (Trombone).
Responsável pelo fast-drop triage: descarta comentários neutros antes de gastar
tokens do pipeline de IA cloud.

Arquitetura:
  - Stateless por design: cria um corpus inline a cada lote e o descarta.
  - Fallback silencioso: se o Voyant estiver offline, retorna None para que
    o caller (run_batch_classification) envie 100% ao LLM normalmente.
  - Compatível com asyncio: usa httpx.AsyncClient para não bloquear o event loop.

Pré-requisito: VoyantServer.jar rodando localmente (gerenciado pelo Watchdog).
"""
import os
import json
import logging
import asyncio
from typing import Optional

import httpx

logger = logging.getLogger("core.voyant_service")

# ---------------------------------------------------------------------------
# Dicionário de termos hostis calibrado para o contexto político brasileiro.
# Cruzado contra os top-N termos TF-IDF retornados pelo Trombone.
# Fonte: custom_rules.json + análise dos datasets MCA v2.2.
# ---------------------------------------------------------------------------
HOSTILE_LEXICON: set[str] = {
    # Violência / Ameaça
    "tiro", "bala", "matar", "morte", "morrer", "morre", "enforcar", "forca",
    "preso", "prender", "cadeia", "assassino", "assassinar",
    # Insulto ad hominem grave
    "lixo", "idiota", "imbecil", "burro", "incompetente", "vagabundo",
    "bandido", "ladrão", "roubar", "corrupto", "corrupção",
    # Ódio identitário / gênero
    "macaco", "nordestino", "favelado", "safada", "piranha", "puta", "vagabunda",
    # Ataque institucional
    "golpe", "ditadura", "fraudar", "fraude", "fraudes", "urna", "golpista",
    # Dano à imagem / acusações criminais
    "pedofil", "pedofilia", "genocida", "genocídio", "traidor", "traição",
    "terrorista", "terrorismo", "quadrilha", "esquema",
}

# Limiar: se a proporção de termos hostis no vocabulário TF-IDF
# for inferior a este valor, o lote é marcado como NEUTRO (fast-drop).
HOSTILE_RATIO_THRESHOLD = float(os.getenv("VOYANT_HOSTILE_THRESHOLD", "0.08"))

# Quantos termos de alto TF-IDF solicitar ao Trombone por lote.
TROMBONE_LIMIT = int(os.getenv("VOYANT_TROMBONE_LIMIT", "50"))

# v92.2: Usar 127.0.0.1 para evitar problemas de resolução/fallback de httpx (RuntimeError)
VOYANT_BASE_URL = os.getenv("VOYANT_BASE_URL", "http://127.0.0.1:8888/trombone")
VOYANT_TIMEOUT = float(os.getenv("VOYANT_TIMEOUT", "8.0"))


class VoyantService:
    """
    Cliente assíncrono para a API Trombone do VoyantServer local.
    """

    def __init__(self, base_url: str = VOYANT_BASE_URL, timeout: float = VOYANT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Retorna o cliente HTTP, criando-o lazily na primeira chamada."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Encerra o cliente HTTP. Chamar no teardown do worker."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # API Pública
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """
        Verifica se o Trombone está respondendo.
        Retorna True se o servidor estiver operante, False caso contrário.
        """
        try:
            client = self._get_client()
            # A rota base com format=json retorna 200 OK e metadados da versão
            resp = await client.get(self.base_url, params={"format": "json"})
            return resp.status_code == 200 and "voyantVersion" in resp.text
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    async def extract_corpus_terms(self, texts: list[str]) -> Optional[dict]:
        """
        Envia um lote de textos para o Trombone e retorna os top-N termos.
        """
        if not texts:
            return {}

        clean_texts = [t.strip() for t in texts if t and t.strip()]
        if not clean_texts:
            return {}

        params = {
            "tool": "corpus.CorpusTerms",
            "format": "json",
            "limit": TROMBONE_LIMIT,
            "sort": "RELATIVEFREQ",
        }
        # v92.2: Passar múltiplos documentos usando lista no dicionário 'data'.
        # Isso garante compatibilidade com o parse assíncrono do httpx e cria
        # documentos separados no Trombone para um IDF preciso por lote.
        data = {"string": clean_texts}

        try:
            client = self._get_client()
            resp = await client.post(self.base_url, params=params, data=data)
            resp.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("[Voyant] Timeout ao consultar Trombone (%.1fs). Fallback ao LLM.", self.timeout)
            return None
        except httpx.RequestError as exc:
            logger.warning("[Voyant] Erro de conexão com Trombone: %s. Fallback ao LLM.", exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("[Voyant] HTTP %s do Trombone: %s. Fallback ao LLM.", exc.response.status_code, exc)
            return None

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            logger.warning("[Voyant] Resposta do Trombone não é JSON válido: %s", exc)
            return None

        return self._parse_corpus_terms(payload)

    async def triage_batch(self, texts: list[str]) -> Optional[dict]:
        """
        Ponto de entrada principal para o fast-drop triage.
        """
        top_terms = await self.extract_corpus_terms(texts)

        if top_terms is None:
            return None

        if not top_terms:
            logger.debug("[Voyant] Corpus vazio — lote marcado como NEUTRO por padrão.")
            return {"drop": True, "hostile_ratio": 0.0, "hostile_terms": [], "top_terms": {}}

        vocab = set(top_terms.keys())
        hostile_hits = vocab & HOSTILE_LEXICON
        hostile_ratio = len(hostile_hits) / len(vocab) if vocab else 0.0

        should_drop = hostile_ratio < HOSTILE_RATIO_THRESHOLD

        if should_drop:
            logger.info(
                "[Voyant] ✅ Fast-drop: ratio=%.2f%% (<%s%%) — lote NEUTRO, pulando LLM.",
                hostile_ratio * 100,
                HOSTILE_RATIO_THRESHOLD * 100,
            )
        else:
            logger.info(
                "[Voyant] ⚠️ Vocabulário hostil detectado: ratio=%.2f%% — delegando ao LLM. Termos: %s",
                hostile_ratio * 100,
                ", ".join(sorted(hostile_hits)[:10]),
            )

        return {
            "drop": should_drop,
            "hostile_ratio": hostile_ratio,
            "hostile_terms": sorted(hostile_hits),
            "top_terms": top_terms,
        }

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _parse_corpus_terms(self, payload: dict) -> dict:
        """
        Normaliza a resposta JSON do Trombone (corpus.CorpusTerms).
        """
        result: dict = {}

        try:
            terms_list = (
                payload
                .get("corpusTerms", {})
                .get("terms", [])
            )

            if terms_list:
                for entry in terms_list:
                    term = entry.get("term", "").lower().strip()
                    score = float(entry.get("relativeFreq", entry.get("rawFreq", 0)))
                    if term and len(term) > 2:
                        result[term] = score
                return result

            alt_terms = payload.get("terms", [])
            if isinstance(alt_terms, list):
                for entry in alt_terms:
                    if isinstance(entry, dict):
                        term = entry.get("term", "").lower().strip()
                        score = float(entry.get("relativeFreq", entry.get("rawFreq", 0)))
                        if term and len(term) > 2:
                            result[term] = score

        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("[Voyant] Falha ao parsear resposta do Trombone: %s. Payload: %s", exc, str(payload)[:200])

        return result


# Instância singleton
voyant_service = VoyantService()
