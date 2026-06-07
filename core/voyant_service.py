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
# Fonte: METODOLOGIA_VICHI_ANALITICA.md, ADENDO_LINGUISTICA_PROFUNDA.md,
#        PADRONIZACAO_LINGUISTICA_ANALITICA.md (PASA v16.3) + MCA v2.2.
# ---------------------------------------------------------------------------
HOSTILE_LEXICON: set[str] = {
    # === VIOLÊNCIA / AMEAÇA (AMEACA) ===
    "tiro", "bala", "matar", "morte", "morrer", "morre", "enforcar", "forca",
    "preso", "prender", "cadeia", "assassino", "assassinar",
    "morrer", "violencia", "violência", "ameaca", "ameaça", "atacar", "destruir",
    "threat", "violence", "kill", "harm", "assassinato", "incitacao", "incitação",
    "incitar", "terrorismo", "terrorista", "atentado", "massacre", "extermínio",

    # === INSULTO AD HOMINEM GRAVE (INSULTO_AD_HOMINEM) ===
    "lixo", "idiota", "imbecil", "burro", "incompetente", "vagabundo",
    "bandido", "ladrao", "ladrão", "roubar", "corrupto", "corrupcao", "corrupção",
    "estupido", "estúpido", "covarde", "mentiroso", "fraco", "fraude", "traidor",
    "traicao", "traição", "calunia", "calúnia", "difamar", "ofender", "insulto",
    "ofensa", "honra", "competencia", "competência", "aparencia", "aparência",

    # === XENOFOBIA REGIONAL / RACISMO ESTRUTURAL (XENOFOBIA_REGIONAL, RACISMO_ESTRUTURAL) ===
    "nordestino", "nordestina", "pobre", "analfabeto", "ingrato", "miseravel",
    "miserável", "burro", "nao sabe votar", "não sabe votar", "voto de cabresto",
    "macaco", "macaca", "segregacao", "segregação", "injuria", "injúria",
    "racista", "racismo", "racial", "preconceito", "discriminacao", "discriminação",

    # === VIOLÊNCIA DE GÊNERO / MISOGINIA (VIOLÊNCIA_GENERO, MISOGINIA_POLITICA) ===
    "favelado", "favelada", "safada", "piranha", "puta", "vagabunda",
    "machista", "sexista", "misoginia", "machismo", "sexismo", "abuso",
    "feminicidio", "feminicídio", "misogynistic", "patriarcado", "mulheres",
    "doxxing", "redpill", "ataque estetico", "ataque estético", "competencia por genero",

    # === RACISMO RELIGIOSO (RACISMO_RELIGIOSO) ===
    "macumba", "vodu", "voodoo", "magia negra", "demonio", "demônio",
    "guerra espiritual", "intolerancia", "intolerância", "islamofobia",
    "antissemitismo", "religioso", "religiaofobia", "racial slur", "religious slur",

    # === MILÍCIA DIGITAL / ATAQUE INSTITUCIONAL (MILICIA_DIGITAL, ATAQUE_INSTITUCIONAL) ===
    "golpe", "ditadura", "fraudar", "fraude", "fraudes", "urna", "golpista",
    "ditadura do stf", "xandao", "xandão", "intervencao", "intervenção",
    "urls falsas", "url falsa", "fake news", "fake news", "desinformacao",
    "desinformação", "milicia digital", "milícia digital", "bolsonarista",
    "lulista", "petista", "comunista", "fascista", "nazista",
    "corrupto", "incompetente", "deslegitimar", "deslegitimacao", "deslegitimação",
    "crime", "sistema", "sistema politico", "sistema político", "governo",
    "orgaos de estado", "órgãos de estado", "sistema eleitoral", "justica",
    "justiça", "stf", "tse", "congresso", "camara", "câmara", "senado",
    "imprensa", "midia", "mídia", "ciencia", "ciência", "direito",

    # === DANO À IMAGEM / ACUSAÇÕES CRIMINAIS (DANO_A_IMAGEM) ===
    "pedofil", "pedofilia", "genocida", "genocidio", "genocídio", "traidor", "traicao",
    "traição", "terrorista", "terrorismo", "quadrilha", "esquema",
    "crime", "corrupcao", "corrupção", "desvios de conduta", "desvio de conduta",
    "theorize crime", "impute grave misconduct", "fake news", "misinformation",
    "disinformation", "discredit", "escandalo", "escândalo", "acusacoes falsas",
    "acusações falsas", "teorias da conspiracao", "teorias da conspiração",
    "imputacao de crimes", "imputação de crimes", "imputar", "desvios",

    # === FALÁCIAS ARGUMENTATIVAS (Indicadores de coordenação/astroturfing) ===
    "ad hominem", "espantalho", "falsa dicotomia", "ou voce esta", "ou você está",
    "com o povo", "com os criminosos", "nós contra eles", "nos contra eles",
    "generalizacao", "generalização", "exclusao", "exclusão", "silenciamento",

    # === VETOR DE FÚRIA / POLARIZAÇÃO AFETIVA (Engenheiros do Caos) ===
    "desumanizacao", "desumanização", "polarizacao afetiva", "polarização afetiva",
    "engajamento por furia", "engajamento por fúria", "indignacao artificial",
    "indignação artificial", "furia", "fúria", "odio", "ódio", "furioso",
    "performatico", "performático", "performatividade", "deslegitimacao",

    # === N-GRAMAS / COORDENAÇÃO (Slogans de ódio / Astroturfing) ===
    "vamos quebrar tudo", "fora todos", "todos corruptos", "nao presta",
    "não presta", "lixo total", "bandido e ladrão", "corrupto ladrão",
    "eleicao fraudada", "eleição fraudada", "urna fraudada", "voto impresso",
    "intervencao militar", "intervenção militar", "artigo 142", "ai 5",
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
        # inputFormat=text é obrigatório: sem ele o Trombone tenta interpretar
        # o conteúdo do campo `input` como URL ou caminho de arquivo,
        # levantando IllegalArgumentException no DocumentExpander.
        data = {"input": corpus_input, "inputFormat": "text"}

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
