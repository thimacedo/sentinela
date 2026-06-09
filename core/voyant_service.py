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
import time
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
    "crime", "corrupcao", "corrupção", "desvios de conducto", "desvio de conduta",
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
VOYANT_TIMEOUT = float(os.getenv("VOYANT_TIMEOUT", "25.0"))


print(f"[DEBUG] VoyantService loaded from: {__file__}")
class VoyantService:
    """
    Cliente assíncrono para a API Trombone do VoyantServer local.
    """

    def __init__(self, base_url: str = VOYANT_BASE_URL, timeout: float = VOYANT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.is_down = False
        self.last_failed = 0
        self.failure_count = 0
        print(f"[DEBUG] VoyantService instance initialized. Attrs: {dir(self)}")

    async def ping(self) -> bool:
        """
        Verifica se o Trombone está respondendo.
        Retorna True se o servidor estiver operante, False caso contrário.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # A rota base com format=json retorna 200 OK e metadados da versão
                resp = await client.get(self.base_url, params={"format": "json"})
                return resp.status_code == 200 and "voyantVersion" in resp.text
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    async def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= 3:
            self.is_down = True
            self.last_failed = time.time()
            logger.error("[Voyant] 🛑 Circuit Breaker: Voyant desativado temporariamente devido a falhas consecutivas.")

    async def extract_corpus_terms(self, texts: list[str]) -> Optional[dict]:
        # Verificação do Circuit Breaker
        if self.is_down:
            if time.time() - self.last_failed > 600: # Tenta reviver após 10 min
                self.is_down = False
                self.failure_count = 0
            else:
                return None # Fallback imediato

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
        
        import urllib.parse
        encoded_data = urllib.parse.urlencode([("string", t) for t in clean_texts])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                resp = await client.post(self.base_url, params=params, content=encoded_data, headers=headers)
                
                if resp.status_code >= 500:
                    await self._handle_failure()
                    return None
                
                resp.raise_for_status()
                # Se sucesso, reseta contador
                self.failure_count = 0
                
        except (httpx.TimeoutException, httpx.RequestError):
            await self._handle_failure()
            return None
        except httpx.HTTPStatusError:
            await self._handle_failure()
            return None

        try:
            payload = resp.json()
        except json.JSONDecodeError:
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
    # Fase 2 (Opcional) — Colocados para implementação futura
    # ------------------------------------------------------------------

    async def get_collocates(self, texts: list[str], target_word: str) -> list[str]:
        """
        Consulta o CollocatesGraph para encontrar palavras que co-ocorrem
        frequentemente com `target_word` no corpus do lote.
        """
        if not texts or not target_word:
            return []

        clean_texts = [t.strip() for t in texts if t and t.strip()]
        params = {
            "tool": "corpus.CollocatesGraph",
            "format": "json",
            "query": target_word,
            "limit": 20,
        }
        import urllib.parse
        encoded_data = urllib.parse.urlencode([("string", t) for t in clean_texts])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                resp = await client.post(self.base_url, params=params, content=encoded_data, headers=headers)
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


print(f"[DEBUG] VoyantService class definition: {VoyantService}")
print(f"[DEBUG] VoyantService attributes: {dir(VoyantService)}")
# Instância singleton
voyant_service = VoyantService()
print(f"[DEBUG] voyant_service instance attributes: {dir(voyant_service)}")
