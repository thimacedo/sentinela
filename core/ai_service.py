# -*- coding: utf-8 -*-
"""
PASA v52.5 - AI Service: Motor de Inteligencia Resiliente (Unified Rotation Queue)
Correcoes v1.0: ContextClassifier para mitigacao de falsos positivos em contextos positivos.
Roteamento dinamico unificado com atraso rigido anti-429, cache I/O, e fallback integrado.
"""
import os
import json
import logging
import asyncio
import traceback
import re
import codecs
import time
import random
import httpx
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

logger = logging.getLogger("AIService")

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD_DATASET_PATH = os.path.join(BASE_DIR, "data", "classifier_gold_dataset.json")
MD_PATH = os.path.join(BASE_DIR, "docs", "PADRONIZACAO_LINGUISTICA_ANALITICA.md")
CUSTOM_RULES_PATH = os.path.join(BASE_DIR, "config", "custom_rules.json")
# Contexto linguistico forense centralizado (PASA v51.0)
CONTEXTO_CLASSIFICACAO_PATH = os.path.join(BASE_DIR, "bases_pdf", "CONTEXTO_CLASSIFICACAO.md")
_CONTEXTO_CACHE: str = ""

# ============================================================================
# ContextClassifier v1.0: Detector de Contextos Positivos
# Mitigacao de falsos positivos em textos claramente benignos (aniversario, etc.)
# ============================================================================
POSITIVE_CONTEXT_PATTERNS = [
    r'\bparab[eé]ns\b.*\b(?:anivers[áa]rio|amigo|irm[ãa]o|vida|felicidades?)\b',
    r'\bfeliz\s+(?:anivers[áa]rio|niver|dia|Natal|ano novo|P[áa]scoa)\b',
    r'\bmuitos\s+(?:anos\s+de\s+vida)\b',
    r'\btudo\s+de\s+bom\b',
    r'\b(?:Deus|Jesus)\s+aben[çc]oe\b',
    r'\b(?:obrigad[ao]|agrade[çc]o)\b.*\b(?:Deus|aben[çc]oad[ao]|feliz)\b',
    r'\b(?:for[çc]a|apoio|estamos\s+juntos)\b.*\b(?:amigo|irm[ãa]o)\b',
    r'\b(?:bom\s+dia|boa\s+tarde|boa\s+noite)\b.*\b(?:aben[çc]oad[ao]|lindo|maravilhoso)\b',
    r'^[🎉🎂🎁🙌👏🥳🎊🎈✨🙏❤️💖💕]+.*\b(?:parab[eé]ns|feliz|bom|lindo)\b',
]

_compiled_positive_patterns = [re.compile(p, re.IGNORECASE) for p in POSITIVE_CONTEXT_PATTERNS]

POSITIVE_CONTEXT_KEYWORDS = {'aniversario', 'parabens', 'feliz_aniversario', 'niver', 'felicidades', 'abençoe', 'realizações'}

NEGATIVE_INDICATORS_IN_POSITIVE = {
    'bandido', 'ladrão', 'ladráo', 'corrupto', 'verme', 'lixo', 'vagabundo', 'idiota', 'imbecil',
    'burro', 'morte', 'matar', 'assassino', 'golpista', 'ditadura', 'fraude', 'crime',
    'odio', 'ódio', 'racista', 'homofobia', 'xenofobia', 'preconceito', 'discriminação',
    'discriminacao', 'vergonha', 'nojo', 'asqueroso', 'repugnante',
}


class ContextClassifier:
    """Detector deterministico de contextos pragmaticos positivos."""

    @staticmethod
    def is_positive_context(text: str) -> bool:
        if not text or len(text.strip()) < 3:
            return False
        text_lower = text.lower()
        for neg in NEGATIVE_INDICATORS_IN_POSITIVE:
            if neg in text_lower:
                return False
        positive_pattern_matches = sum(1 for p in _compiled_positive_patterns if p.search(text))
        words = set(re.findall(r'\b\w+\b', text_lower))
        keyword_matches = words & POSITIVE_CONTEXT_KEYWORDS
        if (positive_pattern_matches >= 1 and len(keyword_matches) >= 1) or positive_pattern_matches >= 2:
            return True
        if len(words) <= 20 and 'parabens' in words:
            if words & {'amigo', 'irmão', 'irmao', 'parceiro', 'querido', 'querida', 'brother'}:
                return True
        return False


def _load_contexto_classificacao() -> str:
    global _CONTEXTO_CACHE
    if _CONTEXTO_CACHE:
        return _CONTEXTO_CACHE
    try:
        if os.path.exists(CONTEXTO_CLASSIFICACAO_PATH):
            with open(CONTEXTO_CLASSIFICACAO_PATH, "r", encoding="utf-8") as f:
                _CONTEXTO_CACHE = f.read()
                logger.info(f"[AI] CONTEXTO_CLASSIFICACAO carregado ({len(_CONTEXTO_CACHE)} chars).")
        else:
            logger.warning("[AI] CONTEXTO_CLASSIFICACAO.md nao encontrado.")
    except Exception as e:
        logger.warning(f"[AI] Erro ao carregar CONTEXTO_CLASSIFICACAO.md: {e}")
    return _CONTEXTO_CACHE


SYSTEM_PROMPT = """Voce eh um analista especializado em Linguistica Analitica Digital baseado no Metodo Vichi-Sentinela para identificacao de ataques coordenados e hostilidade politica.
Sua missao eh classificar comentarios com realismo absoluto, seguindo a Metodologia de Classificacao de Ataques (MCA v2.4).

--- REGRAS DE OURO ---
1. REALISMO: Nao ignore ataques velados, ironias destrutivas ou acusacoes de corrupcao/crime.
2. FALSA EQUIVALENCIA E IDENTIDADE: Se o texto associar uma minoria (genero, sexualidade, raca) a palavra 'crime' ou 'aberracao' (ex: 'ser gay nao eh crime mas querer obrigar a aceitar crimes praticados por eles', 'eh uma aberracao'), a categoria DEVE ser ODIO_IDENTITARIO. Isso NAO E opiniao politica neutra.
3. OBFUSCACAO E LEETSPEAK: Textos que usam V5RM5, LIX0, V44G4BUND0 sao INSULTOS (Verme, Lixo, Vagabundo). Avalie o significado decodificado e classifique como INSULTO_AD_HOMINEM.
4. FALSAS ANALISES: O uso de jargao juridico para "teorizar" ou acusar o alvo de crimes (traicao, assassinato, corrupcao) eh um ataque direto e deve ser classificado como DANO_A_IMAGEM.
5. COMUNICACAO: Se detectar uma imputacao de ato ilicito, voce NAO DEVE usar a palavra "crime" na sua analise.
6. ATAQUES INSTITUCIONAIS DIRETOS: Associar tribunais superiores (ex: STF, TSE) ou o sistema democratico a faccoes, ditaduras ou crimes (ex: "tribunal do crime", "ditadura do STF") DEVE ser classificado incondicionalmente como ATAQUE_INSTITUCIONAL (is_hate: true).
7. IDIOMA: Sua resposta (incluindo a analise_pericial) deve ser 100% em Portugues Brasileiro (pt-BR).

--- CONTEXTOS POSITIVOS (NOVO v1.0) ---
Os textos abaixo NAO SAO discurso de odio. Classifique como NEUTRO (is_hate: false):
- Mensagens de aniversario: "Parabens", "Feliz aniversario", "Muitos anos de vida"
- Agradecimentos e bençãos: "Deus abençoe", "Obrigado amigo", "Tudo de bom"
- Saudacoes positivas: "Bom dia abençoado", "Boa tarde a todos"
- Expressoes de apoio nao agressivas: "Forca amigo", "Estamos juntos" (SEM insultos)
- IMPORTANTE: "Parabens" em contexto de aniversario ou celebracao pessoal eh SEMPRE NEUTRO.
  Nao confunda com sarcasmo politico. Se o texto nao contiver ataque, insulto ou acusacao,
  e for claramente uma mensagem de carinho/celebracao, classifique como NEUTRO.

--- CATEGORIZACAO (MCA v2.4) ---
Se o comentario for hostil (is_hate: true), escolha obrigatoriamente UMA chave exata:
- ODIO_IDENTITARIO: Ataques ou falsa equivalencia moral contra raca, religiao, orientacao sexual (homofobia), misoginia ou regionalismo.
- VIOLENCIA_GENERO: Ofensas focadas na condicao feminina.
- AMEACA: Incitacao a dano fisico, violencia fisica ou morte.
- INSULTO_AD_HOMINEM: Desumanizacao (verme, lixo), baixo calao, ataques a honra, aparencia ou competencia.
- ATAQUE_INSTITUCIONAL: Deslegitimacao de orgaos de Estado ou do sistema democratico.
- DANO_A_IMAGEM: Acusacoes de corrupcao, roubo ou infracoes graves contra o alvo.

Se o comentario NAO for hostil (is_hate: false), use:
- NEUTRO: Expressoes de engajamento, slogans ou criticas tecnicas, mensagens de carinho, aniversario, agradecimentos.

--- FORMATO DE RESPOSTA (JSON APENAS) ---
{
  "is_hate": boolean,
  "categoria_ia": "ODIO_IDENTITARIO|VIOLENCIA_GENERO|AMEACA|INSULTO_AD_HOMINEM|ATAQUE_INSTITUCIONAL|DANO_A_IMAGEM|NEUTRO",
  "confianca_ia": float,
  "analise_pericial": "Explicacao curta (sem usar a palavra crime)."
}
"""

LOCAL_SYSTEM_PROMPT = """Voce eh um classificador binario de hostilidade politica baseado no Metodo Vichi-Sentinela.
Atencao redobrada a:
1. Obfuscacao (ex: V5RM5 = Verme -> SUSPEITO).
2. Associacao de minorias a crimes ou a termo 'aberracao' (Homofobia velada -> SUSPEITO).
3. Ataques a instituicoes democraticas, como associar STF/TSE a faccoes (ex: 'tribunal do crime') ou ditadura -> SUSPEITO.
Analise se o texto contem: insultos reais, ameacas, acusacoes de corrupcao ou deslegitimacao.

--- CONTEXTOS POSITIVOS (NOVO v1.0) ---
NAO marque como SUSPEITO textos que sao claramente:
- Mensagens de aniversario: "Parabens amigo", "Feliz aniversario"
- Agradecimentos: "Deus abençoe", "Obrigado", "Tudo de bom"
- Saudacoes positivas: "Bom dia abençoado"
- Expressoes de carinho/apoio SEM insultos

Responda APENAS com JSON:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO|LIXO|SUSPEITO",
  "confianca_ia": float,
  "analise_pericial": "Motivo rapido (sem usar a palavra crime)"
}
IMPORTANTE: Se houver QUALQUER sinal de ataque, obfuscacao ou hostilidade identitaria, marque como "SUSPEITO". Mas se for claramente uma mensagem de aniversario, parabens ou agradecimento, marque como NEUTRO.
"""

def safe_decode_unicode(s: str) -> str:
    try:
        def decode_escapes(match):
            try:
                return codecs.decode(match.group(0), 'unicode-escape')
            except Exception:
                return match.group(0)
        pattern = r'\\u[dD][89abAB][0-9a-fA-F]{2}\\u[dD][cdefCDEF][0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}'
        decoded = re.sub(pattern, decode_escapes, s)
        return decoded.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return s

def clean_null_chars(data: Any) -> Any:
    if isinstance(data, str):
        return data.replace("\u0000", "").replace("\x00", "")
    elif isinstance(data, list):
        return [clean_null_chars(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_null_chars(value) for key, value in data.items()}
    return data


class AIService:
    def __init__(self):
        self.ollama_client = None
        self.mistral_client = None
        self.providers = []
        self.consecutive_failures: Dict[str, int] = {}
        self.fallback_llm = None
        self.current_provider_idx = 0
        self._prompt_cache = {"enriched_local": None, "enriched_cloud": None}
        self.refresh_prompt_cache()

    def _get_next_provider(self):
        now = time.time()
        healthy = [p for p in self.providers if p["cooldown_until"] <= now]
        if not healthy:
            return None
        self.current_provider_idx = (self.current_provider_idx + 1) % len(healthy)
        return healthy[self.current_provider_idx]

    def _ensure_clients(self):
        if self.ollama_client is None:
            self.ollama_client = AsyncOpenAI(
                api_key="ollama",
                base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
                max_retries=2,
                http_client=httpx.AsyncClient(timeout=httpx.Timeout(timeout=300.0, connect=60.0))
            )
        if self.mistral_client is None:
            self.mistral_client = AsyncOpenAI(
                api_key=os.getenv("MISTRAL_API_KEY") or "dummy-mistral-key",
                base_url="https://api.mistral.ai/v1",
                max_retries=0
            )
        if not self.providers:
            finetuned_model = os.getenv('FINETUNED_MODEL_NAME', "open-mistral-nemo")
            self.providers = [
                {"name": "mistral", "client": self.mistral_client, "model": finetuned_model, "timeout": 30.0, "cooldown_until": 0.0, "is_async_openai": True},
            ]
            alibaba_key = os.getenv("ALIBABA_API_KEY") or ""
            if alibaba_key:
                self.providers.append({
                    "name": "alibaba",
                    "client": AsyncOpenAI(api_key=alibaba_key, base_url="https://ws-718h73opsywfpzbv.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"),
                    "model": "qwen-max", "timeout": 45.0, "cooldown_until": 0.0, "is_async_openai": True
                })
            self.providers.append({
                "name": "ollama", "client": self.ollama_client, "model": "phi3",
                "timeout": 30.0, "cooldown_until": 0.0, "is_async_openai": True
            })
            if os.getenv("GEMINI_API_KEY"):
                self.providers.append({"name": "gemini-2.5-flash", "client": None, "model": "gemini-2.5-flash", "timeout": 45.0, "cooldown_until": 0.0, "is_async_openai": False})
            if os.getenv("ANTHROPIC_API_KEY"):
                self.providers.append({"name": "claude-3-5-sonnet", "api_key": os.getenv("ANTHROPIC_API_KEY"), "client": None, "model": "claude-3-5-sonnet", "timeout": 45.0, "cooldown_until": 0.0, "is_async_openai": False})
            try:
                from core.config import FALLBACK_PROVIDERS
                for prov in FALLBACK_PROVIDERS:
                    if not any(p["name"] == prov["name"] for p in self.providers):
                        api_key_env = prov.get("api_key_env")
                        if api_key_env and not os.getenv(api_key_env):
                            continue
                        self.providers.append({"name": prov["name"], "model": prov.get("model", ""), "timeout": 45.0, "cooldown_until": 0.0, "is_async_openai": False})
            except Exception as e:
                logger.warning(f"[AI] Falha ao injetar FALLBACK_PROVIDERS: {e}")

    def refresh_prompt_cache(self) -> None:
        self._prompt_cache["enriched_local"] = self._build_enrichment(is_local=True)
        self._prompt_cache["enriched_cloud"] = self._build_enrichment(is_local=False)
        logger.debug("[AI] Cache de prompts recarregado.")

    def _build_enrichment(self, is_local: bool) -> str:
        base_prompt = LOCAL_SYSTEM_PROMPT if is_local else SYSTEM_PROMPT
        if is_local:
            enrichment = "\n\n--- DIRETRIZES ESSENCIAIS (TRIAGEM LOCAL) ---\n"
            enrichment += "- Foque em detectar INSULTOS, AMEACAS e ACUSACOES GRAVES.\n"
            enrichment += "- Se houver hostilidade clara, marque como SUSPEITO.\n"
            enrichment += "- Criticas normais e slogans sao NEUTRO.\n"
            enrichment += "- XENOFOBIA: termos como 'nordestino ingrato/analfabeto/burro' = SUSPEITO.\n"
            enrichment += "- IRONIA: 'Que genio, so faliu 3 empresas!' eh insulto velado = SUSPEITO.\n"
            enrichment += "- HYPE POSITIVO: 'Matou no debate! Bomba de boa!' = NEUTRO.\n"
            enrichment += "- ANIVERSARIO/CELEBRACAO: 'Parabens amigo', 'Feliz aniversario' = NEUTRO.\n"
            enrichment += "- AGRADECIMENTO: 'Deus abençoe', 'Obrigado', 'Tudo de bom' = NEUTRO.\n"
            return base_prompt + enrichment
        contexto = _load_contexto_classificacao()
        if contexto:
            enrichment = "\n\n--- CONTEXTO LINGUISTICO FORENSE (PASA v51.0) ---\n" + contexto + "\n"
        else:
            enrichment = "\n\n--- PADRONIZACAO LINGUISTICA ANALITICA (MD) ---\n"
            if os.path.exists(MD_PATH):
                try:
                    with open(MD_PATH, "r", encoding="utf-8") as f:
                        enrichment += f.read() + "\n"
                except Exception as e:
                    logger.warning(f"[AI] Erro ao ler {MD_PATH}: {e}")
            else:
                enrichment += "(Arquivo nao encontrado)\n"
        if os.path.exists(CUSTOM_RULES_PATH):
            try:
                with open(CUSTOM_RULES_PATH, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                enrichment += "\n--- DIRETRIZES ADICIONAIS (PASA EXTRA) ---\n"
                if "additional_rules" in rules and rules["additional_rules"]:
                    enrichment += "Regras:\n" + "\n".join(f"- {r}" for r in rules["additional_rules"]) + "\n"
                if "mitigate_false_positives" in rules and rules["mitigate_false_positives"]:
                    enrichment += "Blindagem contra Falsos Positivos:\n" + "\n".join(f"- {r}" for r in rules["mitigate_false_positives"]) + "\n"
                if "custom_keywords" in rules and rules["custom_keywords"]:
                    enrichment += "Dicionario Lexico:\n" + "\n".join(f"- Categoria {cat}: {', '.join(kw)}" for cat, kw in rules["custom_keywords"].items()) + "\n"
            except Exception as e:
                logger.warning(f"[AI] Erro ao carregar {CUSTOM_RULES_PATH}: {e}")
        if not is_local and os.path.exists(GOLD_DATASET_PATH):
            try:
                with open(GOLD_DATASET_PATH, "r", encoding="utf-8") as f:
                    gold_data = json.load(f)
                if isinstance(gold_data, list) and gold_data:
                    examples = [f"- Texto: \"{str(i.get('text', ''))[:240]}\" -> Categoria: {str(i.get('label', '')).upper()}" for i in gold_data[-10:] if i.get("text") and i.get("label")]
                    if examples:
                        enrichment += "\n\n--- PADRAO OURO ---\nUse como calibracao:\n" + "\n".join(examples) + "\n"
            except Exception as e:
                logger.warning(f"[AI] Erro ao carregar {GOLD_DATASET_PATH}: {e}")
        if "--- FORMATO DE RESPOSTA (JSON APENAS) ---" in base_prompt:
            parts = base_prompt.split("--- FORMATO DE RESPOSTA (JSON APENAS) ---")
            return parts[0] + enrichment + "\n--- FORMATO DE RESPOSTA (JSON APENAS) ---" + parts[1]
        return base_prompt + enrichment

    def _get_system_prompt(self, is_local: bool) -> str:
        cache_key = "enriched_local" if is_local else "enriched_cloud"
        if not self._prompt_cache.get(cache_key):
            self.refresh_prompt_cache()
        return self._prompt_cache[cache_key]

    def _rotate_provider(self, name: str, reason: str = "") -> None:
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            self.providers.append(prov)
            logger.debug(f"[AI] Provedor '{name}' rotacionado. Motivo: {reason}")

    def _remove_provider(self, name: str, reason: str = "") -> None:
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            logger.warning(f"[AI] Provedor '{name}' REMOVIDO. {reason}")

    def _handle_provider_error(self, provider: Dict[str, Any], exception: Exception) -> bool:
        import httpx
        name = provider["name"]
        status_code = getattr(exception, "status_code", None)
        if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
            status_code = exception.response.status_code
        if name == "ollama" and isinstance(exception, (httpx.ConnectError, httpx.ConnectTimeout)):
            status_code = 503
        self.consecutive_failures[name] = self.consecutive_failures.get(name, 0) + 1
        ai_circuit_breaker.record_failure(name, status_code if status_code else 500)
        if name == "ollama" and not ai_circuit_breaker.can_execute(name):
            try:
                from watchdog import send_whatsapp_alert
                send_whatsapp_alert("Sentinela: Ollama local falhou criticamente. Intervencao manual requerida.", category="ollama_down")
            except Exception as alert_err:
                logger.error(f"[AI] Erro ao enviar alerta: {alert_err}")
        if status_code in [400, 401, 402, 403, 404]:
            if name == "ollama":
                provider["cooldown_until"] = time.time() + 300.0
                return False
            else:
                self._remove_provider(name, f"Erro Critico ({status_code})")
                return True
        if status_code == 429:
            provider["cooldown_until"] = time.time() + 300.0
        else:
            provider["cooldown_until"] = time.time() + 30.0
        self._rotate_provider(name, f"Falha - {str(exception)[:100]}")
        return False

    async def _execute_provider_call(self, provider: Dict[str, Any], final_system_prompt: str, user_content: str, response_format: str, comment_id: str = None, candidato_id: str = None) -> str:
        self._ensure_clients()
        name = provider["name"]
        if name == "ollama":
            from core.health_check import ensure_ollama_running
            ensure_ollama_running()
        if provider.get("is_async_openai", False):
            kwargs = {
                "model": provider["model"],
                "messages": [{"role": "system", "content": final_system_prompt}, {"role": "user", "content": user_content}],
                "temperature": 0.0,
                "timeout": provider.get("timeout", 15.0)
            }
            if response_format and response_format != "text":
                kwargs["response_format"] = {"type": response_format}
            response = await provider["client"].chat.completions.create(**kwargs)
            return response.choices[0].message.content
        else:
            if self.fallback_llm is None:
                from core.fallback_llm import FallbackLLM
                self.fallback_llm = FallbackLLM()
            fallback_text = f"{final_system_prompt}\n\nUser: \"{user_content}\"\n\nResponda estritamente no formato exigido."
            return await asyncio.to_thread(self.fallback_llm.classify, fallback_text, name, comment_id, candidato_id)

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        return await self.classify_text(text, comment_id)

    async def chat_completion(self, prompt: str, system_prompt: str = "Voce eh um assistente tecnico...", response_format: str = "json_object") -> Optional[Dict[str, Any]]:
        active_providers = [p for p in self.providers if p["name"] != "ollama"]
        if not active_providers:
            active_providers = list(self.providers)
        max_attempts = len(active_providers)
        for _ in range(max_attempts):
            provider = active_providers[0]
            name = provider["name"]
            if not ai_circuit_breaker.can_execute(name):
                active_providers.remove(provider)
                active_providers.append(provider)
                self._rotate_provider(name, "Circuito Aberto")
                continue
            now = time.time()
            if now < provider.get("cooldown_until", 0.0):
                await asyncio.sleep(provider["cooldown_until"] - now)
            try:
                base_sys = self._get_system_prompt(is_local=False)
                final_system_prompt = f"{system_prompt}\n\n{base_sys}" if system_prompt not in base_sys else base_sys
                content = await self._execute_provider_call(provider, final_system_prompt, prompt, response_format)
                provider["cooldown_until"] = time.time() + 1.0
                self.consecutive_failures[name] = 0
                ai_circuit_breaker.record_success(name)
                self._rotate_provider(name, "Sucesso")
                active_providers.remove(provider)
                active_providers.append(provider)
                return json.loads(content) if response_format == "json_object" else {"content": content}
            except Exception as e:
                was_removed = self._handle_provider_error(provider, e)
                active_providers.remove(provider)
                if not was_removed:
                    active_providers.append(provider)
                continue
        return None

    async def classify_text(self, text: str, comment_id: str = "N/A", trace_id: str = None, force_cloud: bool = False, force_local: bool = False, candidato_id: str = None) -> Dict[str, Any]:
        self._ensure_clients()
        if not isinstance(text, str):
            text = str(text or "")
        text = text.strip()
        if not text:
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Texto vazio.", "name": "guard"}
        if len(text) > 8000:
            text = text[:8000]

        # FIX v1.0: ContextClassifier - Detector de contextos positivos
        if ContextClassifier.is_positive_context(text):
            logger.info(f"[AI:ContextClassifier] Contexto positivo detectado para ID {comment_id}. Pulando LLM.")
            return {
                "is_hate": False,
                "categoria_ia": "NEUTRO",
                "confianca_ia": 0.99,
                "analise_pericial": "Contexto benigno detectado: celebracao/agradecimento/parabens. [ContextClassifier v1.0]",
                "name": "context_classifier"
            }

        def decode_leetspeak(t: str) -> str:
            replacements = {'5': 'S', '4': 'A', '3': 'E', '1': 'I', '0': 'O', '7': 'T', '8': 'B'}
            words = t.split()
            decoded_words = []
            for w in words:
                if any(c.isdigit() for c in w) and any(c.isalpha() for c in w):
                    for k, v in replacements.items():
                        w = w.replace(k, v)
                decoded_words.append(w)
            return " ".join(decoded_words)

        decoded_text = decode_leetspeak(text)

        from core.lexical_filter import lexical_filter
        if lexical_filter.is_junk(decoded_text):
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Filtro lexico.", "name": "lexical"}

        if os.getenv("USE_DSPY", "false").lower() == "true":
            try:
                from core.dspy_integration import DSpyClassifierEngine
                engine = DSpyClassifierEngine(self)
                res_dspy = await engine.classificar(decoded_text, force_local=force_local, force_cloud=force_cloud)
                if res_dspy and res_dspy.get("success", False):
                    res_dspy["name"] = "dspy-mesh"
                    return res_dspy
            except Exception as e_dspy:
                logger.warning(f"[AI] Falha no DSPy: {e_dspy}")

        allowed_providers = self.providers
        if force_cloud:
            allowed_providers = [p for p in self.providers if p["name"] != "ollama"]
        elif force_local:
            allowed_providers = [p for p in self.providers if p["name"] == "ollama"]
        if not allowed_providers:
            allowed_providers = self.providers

        res = None
        for _ in range(len(allowed_providers)):
            now = time.time()
            healthy = [p for p in allowed_providers if p["cooldown_until"] <= now]
            if not healthy:
                await asyncio.sleep(5)
                provider = allowed_providers[0]
            else:
                provider = healthy[self.current_provider_idx % len(healthy)]
                self.current_provider_idx += 1
            name = provider["name"]
            try:
                is_local = "ollama" in name
                final_system_prompt = self._get_system_prompt(is_local)
                user_content = f"Texto: \"{decoded_text}\""
                content = await self._execute_provider_call(provider, final_system_prompt, user_content, "json_object", comment_id, candidato_id)
                res = self._parse_json_response(content)
                res["name"] = name
                if res and res.get("categoria_ia") != "ERRO":
                    return res
            except Exception as e:
                self._handle_provider_error(provider, e)
                continue
        return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 0.0, "analise_pericial": "Falha geral nos provedores.", "name": "failover"}

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        allowed_categories = {"ODIO_IDENTITARIO", "VIOLENCIA_GENERO", "AMEACA", "INSULTO_AD_HOMINEM", "ATAQUE_INSTITUCIONAL", "DANO_A_IMAGEM", "NEUTRO", "LIXO", "SUSPEITO", "ERRO"}
        fallback = {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 0.5, "analise_pericial": "Erro parser."}
        parsed = None
        try:
            parsed = json.loads(content)
        except Exception:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception as e:
                    logger.warning(f"[AI] Falha no fallback JSON parser: {e}")
        if not isinstance(parsed, dict):
            return fallback
        category = str(parsed.get("categoria_ia", "")).upper().strip()
        if category not in allowed_categories:
            category = "ERRO"
        confidence = parsed.get("confianca_ia", 0.5)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.5
        confidence = max(0.0, min(confidence, 1.0))
        # FIX v1.0: SUSPEITO nao eh discurso de odio
        is_hate = bool(parsed.get("is_hate", False))
        if category in {"NEUTRO", "LIXO", "SUSPEITO"}:
            is_hate = False
        analise = str(parsed.get("analise_pericial", "")).strip() or "Sem analise."
        return {"is_hate": is_hate, "categoria_ia": category, "confianca_ia": confidence, "analise_pericial": analise}

    async def run_batch_classification(self, limit: int = 50) -> int:
        try:
            from core.db import db_client
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id, texto_bruto, trace_id, candidato_id').eq('processado_ia', False).limit(limit).execute
            )
            items = res.data or []
            if not items:
                return 0
            try:
                from core.voyant_service import voyant_service
                texts = [item["texto_bruto"] for item in items]
                triage = await voyant_service.triage_batch(texts)
            except Exception as _voyant_exc:
                logger.warning("[AI:Batch] Voyant falhou: %s", _voyant_exc)
                triage = None
            force_local_batch = False
            force_cloud_batch = False
            if triage is not None:
                if triage["drop"]:
                    logger.info("[AI:Voyant] Lote NEUTRO. Redirecionando para Ollama local.")
                    force_local_batch = True
                else:
                    logger.info("[AI:Voyant] Vocabulario hostil detectado. Delegando ao LLM.")
                    force_cloud_batch = True
            count = 0
            semaphore = asyncio.Semaphore(5)
            async def _process_single(item):
                async with semaphore:
                    try:
                        res_ia = await self.classify_text(
                            item["texto_bruto"], item["id"], trace_id=item.get("trace_id"),
                            force_cloud=force_cloud_batch, force_local=force_local_batch,
                            candidato_id=item.get("candidato_id")
                        )
                        if res_ia and res_ia.get("categoria_ia") != "ERRO":
                            engine_name = res_ia.get("name", "unknown").upper()
                            analise = f"[{engine_name}] {res_ia.get('analise_pericial', '')}"
                            analise_ling = {}
                            try:
                                from core.stanza_nlp import stanza_nlp
                                com_hostil = res_ia.get("is_hate", False)
                                analise_ling = stanza_nlp.processar_texto(item["texto_bruto"], include_dependencies=com_hostil)
                            except Exception as e_nlp:
                                logger.warning(f"[AI:Stanza] Falha: {e_nlp}")
                                analise_ling = {"error": str(e_nlp)}
                            await asyncio.to_thread(
                                db_client.client.table('comentarios').update({
                                    "categoria_ia": res_ia["categoria_ia"],
                                    "confianca_ia": res_ia["confianca_ia"],
                                    "is_hate": res_ia["is_hate"],
                                    "analise_pericial": analise,
                                    "processado_ia": True,
                                    "analise_linguistica": analise_ling
                                }).eq("id", item["id"]).execute
                            )
                            if res_ia.get("categoria_ia") == "SUSPEITO":
                                from core.event_bus import local_bus
                                local_bus.signal_new_suspects()
                            try:
                                from core.supabase_service import get_supabase_client
                                db = get_supabase_client()
                                route_decision = "unrouted_llm"
                                if triage is not None:
                                    route_decision = "voyant_local" if force_local_batch else "voyant_cloud"
                                db.table("system_events").insert({
                                    "event_type": "classification_resolved",
                                    "source_module": "ai_service",
                                    "provider_name": res_ia.get("name", "unknown").lower(),
                                    "status": "success",
                                    "metadata": {"route": route_decision, "category": res_ia["categoria_ia"], "confidence": res_ia["confianca_ia"]}
                                }).execute()
                            except Exception as e:
                                logger.error(f"[AI:Batch] Falha telemetria: {e}")
                            return True
                    except Exception as e:
                        if "Colapso" in str(e):
                            raise e
                        logger.debug(f"[AI:Batch] Erro no ID {item['id']}: {e}")
                    return False
            results = await asyncio.gather(*[_process_single(item) for item in items], return_exceptions=True)
            for r in results:
                if isinstance(r, Exception) and "Colapso" in str(r):
                    raise r
                if r is True:
                    count += 1
            return count
        except Exception as e:
            raise e

    async def run_batch_reanalysis(self, limit: int = 15, confidence_threshold: float = 0.6) -> int:
        try:
            from core.db import db_client
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id, texto_bruto, trace_id, candidato_id, analise_pericial, categoria_ia')
                .eq('processado_ia', True).lt('confianca_ia', confidence_threshold).not_.eq('categoria_ia', 'ERRO')
                .order('data_coleta', desc=True).limit(limit).execute
            )
            items = res.data or []
            count = 0
            cloud_providers = [p for p in self.providers if p["name"] != "ollama"]
            if len(cloud_providers) < 2:
                return 0
            for item in items:
                if "[RE-ANALISE:" in (item.get("analise_pericial") or ""):
                    continue
                try:
                    p1, p2 = random.sample(cloud_providers, 2)
                    tasks = [
                        self._execute_provider_call(p1, self._get_system_prompt(False), f"Texto: \"{item['texto_bruto']}\"", "json_object", item['id'], item['candidato_id']),
                        self._execute_provider_call(p2, self._get_system_prompt(False), f"Texto: \"{item['texto_bruto']}\"", "json_object", item['id'], item['candidato_id'])
                    ]
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    valid_res = []
                    for i, r in enumerate(responses):
                        if isinstance(r, Exception): continue
                        parsed = self._parse_json_response(r)
                        parsed["provider"] = [p1, p2][i]["name"]
                        valid_res.append(parsed)
                    if not valid_res: continue
                    final_category = valid_res[0]["categoria_ia"]
                    final_confidence = valid_res[0]["confianca_ia"]
                    final_is_hate = valid_res[0]["is_hate"]
                    engine_tag = valid_res[0]["provider"]
                    if len(valid_res) == 2:
                        if valid_res[0]["categoria_ia"] == valid_res[1]["categoria_ia"]:
                            final_confidence = (valid_res[0]["confianca_ia"] + valid_res[1]["confianca_ia"]) / 2
                            engine_tag = f"CONSENSUS:{valid_res[0]['provider']}+{valid_res[1]['provider']}"
                        else:
                            winner = valid_res[0] if valid_res[0]["confianca_ia"] >= valid_res[1]["confianca_ia"] else valid_res[1]
                            final_category = winner["categoria_ia"]
                            final_confidence = winner["confianca_ia"]
                            final_is_hate = winner["is_hate"]
                            engine_tag = f"SPLIT:WINNER={winner['provider']}"
                    tag_status = "FINALIZADA" if final_confidence < confidence_threshold else "CONCLUIDA"
                    analise = f"[RE-ANALISE:{tag_status}:{engine_tag.upper()}] {valid_res[0].get('analise_pericial', '')}"
                    await asyncio.to_thread(
                        db_client.client.table('comentarios').update({
                            "categoria_ia": final_category, "confianca_ia": final_confidence,
                            "is_hate": final_is_hate, "analise_pericial": analise
                        }).eq("id", item["id"]).execute
                    )
                    count += 1
                    await asyncio.sleep(2.0)
                except Exception as e:
                    if "Colapso" in str(e): break
            return count
        except Exception as e:
            raise e

    async def run_batch_online_review(self, limit: int = 50) -> int:
        try:
            from core.db import db_client
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id, texto_bruto, trace_id, candidato_id').eq('categoria_ia', 'SUSPEITO').limit(limit).execute
            )
            items = res.data or []
            count = 0
            for item in items:
                try:
                    res_ia = await self.classify_text(item["texto_bruto"], item["id"], trace_id=item.get("trace_id"), force_cloud=True, candidato_id=item.get("candidato_id"))
                    if res_ia and res_ia.get("categoria_ia") not in ["ERRO", "SUSPEITO"]:
                        engine_name = res_ia.get("name", "unknown").upper()
                        analise = f"[REVISAO:{engine_name}] {res_ia.get('analise_pericial', '')}"
                        await asyncio.to_thread(
                            db_client.client.table('comentarios').update({
                                "categoria_ia": res_ia["categoria_ia"], "confianca_ia": res_ia["confianca_ia"],
                                "is_hate": res_ia["is_hate"], "analise_pericial": analise, "processado_ia": True
                            }).eq("id", item["id"]).execute
                        )
                        count += 1
                    await asyncio.sleep(2.0)
                except Exception as e:
                    if "Colapso" in str(e):
                        raise e
            return count
        except Exception as e:
            raise e

    async def vision_completion(self, image_b64: str, prompt: str, cache_key: str | None = None, mime_type: str = "image/png") -> dict:
        from core.ai_service_vision_patch import vision_completion as _vision_impl
        return await _vision_impl(self, image_b64, prompt, cache_key, mime_type)

ai_service = AIService()
