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
    # Odio identitário / gênero
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

VOYANT_BASE_URL = os.getenv("VOYANT_BASE_URL", "http://localhost:8888/trombone")
VOYANT_TIMEOUT = float(os.getenv("VOYANT_TIMEOUT", "5.0"))


class VoyantService:
    """
    Cliente assíncrono para a API Trombone do VoyantServer local.

    Uso típico (via fast-drop no run_batch_classification):

        result = await voyant_service.triage_batch(texts)
        if result is None:
            # Voyant offline → fallback: enviar 100% ao LLM
            ...
        elif result["drop"]:
            # Lote classificado como NEUTRO pelo Voyant → pular LLM
            ...
        else:
            # Vocabulário hostil detectado → delegar ao LLM
            ...
    """

    def __init__(self, base_url: str = VOYANT_BASE_URL, timeout: float = VOYANT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        # Cliente HTTP reutilizado por toda a vida do objeto (pool de conexões).
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
            resp = await client.get(self.base_url, params={"tool": "utils.Ping", "format": "json"})
            # O Trombone retorna 200 mesmo em pings — qualquer resposta indica que está vivo.
            return resp.status_code < 500
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    async def extract_corpus_terms(self, texts: list[str]) -> Optional[dict]:
        """
        Envia um lote de textos para o Trombone e retorna os top-N termos
        ordenados por frequência relativa (proxy de TF-IDF no corpus inline).

        Parâmetros:
            texts: lista de strings (comentários brutos do lote).

        Retorna:
            dict no formato { "palavra": score_float } ou None em caso de falha.

        Nota de Engenharia:
            O Trombone não é stateless — ele cria um corpus internamente.
            Para lotes efêmeros (não reutilizados), passamos o texto diretamente
            via `input` e deixamos o servidor descartar ao final da sessão.
            O parâmetro `format=json` é obrigatório; sem ele o retorno é XML.
        """
        if not texts:
            return {}

        # Agrega o lote em um único string separado por parágrafo.
        # O Trombone trata cada bloco separado por \n\n como um "documento" distinto,
        # o que nos dá distribuição IDF correta dentro do lote.
        corpus_input = "\n\n".join(t.strip() for t in texts if t and t.strip())

        params = {
            "tool": "corpus.CorpusTerms",
            "format": "json",
            "limit": TROMBONE_LIMIT,
            "sort": "RELATIVEFREQ",  # Ordena por frequência relativa (equivalente TF-IDF simplificado)
        }
        data = {"input": corpus_input}

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

        Retorna um dict com:
          - "drop": bool — True se o lote pode ser classificado como NEUTRO sem LLM.
          - "hostile_ratio": float — proporção de termos hostis encontrados.
          - "hostile_terms": list[str] — termos hostis identificados no lote.
          - "top_terms": dict — vocabulário completo retornado pelo Trombone.

        Retorna None se o Voyant estiver indisponível (sinal para fallback ao LLM).
        """
        top_terms = await self.extract_corpus_terms(texts)

        if top_terms is None:
            # Voyant offline: o caller deve usar o fallback (LLM 100%).
            return None

        if not top_terms:
            # Corpus vazio ou resposta sem termos: seguro assumir NEUTRO.
            logger.debug("[Voyant] Corpus vazio — lote marcado como NEUTRO por padrão.")
            return {"drop": True, "hostile_ratio": 0.0, "hostile_terms": [], "top_terms": {}}

        # Cruzamento léxico: quantos dos top-N termos batem com o dicionário hostil?
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
    # Fase 2 (Opcional) — Colocados para implementação futura
    # ------------------------------------------------------------------

    async def get_collocates(self, texts: list[str], target_word: str) -> list[str]:
        """
        Consulta o CollocatesGraph para encontrar palavras que co-ocorrem
        frequentemente com `target_word` no corpus do lote.

        Útil para detectar padrões de astroturfing (ex: "fraude" + "urna" + "eleição")
        sem necessitar do LLM.

        Nota: Implementação completa planejada para Fase 2 (PASA v93.0).
        """
        if not texts or not target_word:
            return []

        corpus_input = "\n\n".join(t.strip() for t in texts if t and t.strip())
        params = {
            "tool": "corpus.CollocatesGraph",
            "format": "json",
            "query": target_word,
            "limit": 20,
        }
        data = {"input": corpus_input}

        try:
            client = self._get_client()
            resp = await client.post(self.base_url, params=params, data=data)
            resp.raise_for_status()
            payload = resp.json()
            return self._parse_collocates(payload)
        except Exception as exc:
            logger.debug("[Voyant] Collocates indisponível para '%s': %s", target_word, exc)
            return []

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _parse_corpus_terms(self, payload: dict) -> dict:
        """
        Normaliza a resposta JSON do Trombone (corpus.CorpusTerms) para
        o formato interno { "palavra": score_float }.

        O Trombone retorna estruturas aninhadas que variam com a versão do servidor.
        Este método tenta os dois formatos conhecidos e degrada graciosamente.
        """
        result: dict = {}

        try:
            # Formato principal observado no VoyantServer >= 2.6:
            # { "corpusTerms": { "terms": [ { "term": "palavra", "relativeFreq": 0.002 }, ... ] } }
            terms_list = (
                payload
                .get("corpusTerms", {})
                .get("terms", [])
            )

            if terms_list:
                for entry in terms_list:
                    term = entry.get("term", "").lower().strip()
                    score = float(entry.get("relativeFreq", entry.get("rawFreq", 0)))
                    if term and len(term) > 2:  # Descarta stopwords de 1-2 chars
                        result[term] = score
                return result

            # Formato alternativo (versões mais antigas):
            # { "terms": [ ... ] } na raiz
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

    def _parse_collocates(self, payload: dict) -> list[str]:
        """Extrai lista de termos colocados da resposta do CollocatesGraph."""
        collocates: list[str] = []
        try:
            edges = payload.get("corpusCollocates", {}).get("collocates", [])
            for edge in edges:
                term = edge.get("term", "").lower().strip()
                if term and len(term) > 2:
                    collocates.append(term)
        except (KeyError, TypeError):
            pass
        return collocates


# Instância singleton — mesma convenção do lexical_filter e ai_service do projeto.
voyant_service = VoyantService()
