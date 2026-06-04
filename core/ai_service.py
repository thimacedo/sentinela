"""
PASA v52.4 - AI Service: Motor de Inteligência Resiliente (Unified Rotation Queue)
Roteamento dinâmico unificado com atraso rígido anti-429, cache I/O, e fallback integrado.
"""
import os
import json
import logging
import asyncio
import traceback
import re
import codecs
import time
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

logger = logging.getLogger("AIService")

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD_DATASET_PATH = os.path.join(BASE_DIR, "data", "classifier_gold_dataset.json")
MD_PATH = os.path.join(BASE_DIR, "docs", "PADRONIZACAO_LINGUISTICA_ANALITICA.md")
CUSTOM_RULES_PATH = os.path.join(BASE_DIR, "config", "custom_rules.json")

# MCA v2.2 Protocol - Calibragem Analítica Crítica (v85.11)
SYSTEM_PROMPT = """Você é um perito em Linguística Analítica Digital especializado em ataques coordenados e hostilidade política.
Sua missão é classificar comentários com realismo absoluto, seguindo a Metodologia de Classificação de Ataques (MCA v2.2) e as Diretrizes do Protocolo PASA v16.4.

--- REGRAS DE OURO ---
1. REALISMO: Não ignore ataques velados, ironias destrutivas ou acusações de corrupção/crime.
2. FALSAS PERÍCIAS: O uso de jargão jurídico, citação de artigos penais (CP, CF, Leis) para "teorizar" ou acusar o alvo de traição, assassininato, genocídio ou crimes hediondos NÃO É crítica política legítima. É um ataque direto e deve ser classificado como DANO_A_IMAGEM.
3. DISTINÇÃO: Crítica política legítima foca em IDEIAS. Ataques focam em PESSOAS ou INSTITUIÇÕES.
4. COMUNICAÇÃO: Você é um sistema de INFORMAÇÃO. Se detectar uma imputação de ato ilícito, você NÃO DEVE usar a palavra "crime" na sua classificação ou análise. Você deve rotular como dano à imagem.
5. IDIOMA: Sua resposta (incluindo a analise_pericial) deve ser 100% em Português Brasileiro (pt-BR).

--- CATEGORIZAÇÃO (MCA v2.2) ---
Se o comentário for classificado como hostil (is_hate: true), escolha obrigatoriamente uma das chaves exatas abaixo para "categoria_ia":
- ODIO_IDENTITARIO: Ataques baseados em raça, religião, orientação sexual, misoginia ou XENOFOBIA/REGIONALISMO.
- VIOLENCIA_GENERO: Ofensas focadas na condição feminina.
- AMEACA: Incitação a dano físico, violência física ou morte.
- INSULTO_AD_HOMINEM: Desumanização, baixo calão, ataques à honra, moral, aparência ou competência.
- ATAQUE_INSTITUCIONAL: Deslegitimação de órgãos de Estado, governos ou do sistema democrático.
- DANO_A_IMAGEM: Imputação direta ou uso de teorias jurídicas para acusar o alvo de atos ilícitos, corrupção, roubo ou infrações graves. (IMPORTANTE: Use esta categoria para qualquer acusação que prejudique severamente a imagem do alvo, mas use APENAS este nome de categoria).

Se o comentário NÃO for hostil (is_hate: false), a "categoria_ia" deve ser obrigatoriamente:
- NEUTRO: Expressões de engajamento legítimo, slogans ou críticas técnicas.

--- BLINDAGEM CONTRA FALSOS POSITIVOS ---
Marque como NEUTRO os seguintes cenários:
1. ENTUSIASMO / APOIO (ex: "Vamos pra cima").
2. DEFESA DE MANDATO (opiniões sobre perseguição política).
3. METÁFORAS DE EMBATE (contexto eleitoral).
4. APOIO AGRESSIVO / GÍRIAS (uso de gírias para exaltar o alvo).

--- FORMATO DE RESPOSTA (JSON APENAS) ---
{
  "is_hate": boolean, 
  "categoria_ia": "ODIO_IDENTITARIO|VIOLENCIA_GENERO|AMEACA|INSULTO_AD_HOMINEM|ATAQUE_INSTITUCIONAL|DANO_A_IMAGEM|NEUTRO", 
  "confianca_ia": float,
  "analise_pericial": "Explicação curta (evite usar a palavra crime, foque no impacto informacional)."
}
"""

LOCAL_SYSTEM_PROMPT = """Você é um classificador binário de hostilidade política. 
Analise se o texto contém: insultos reais, ameaças, acusações de atos ilícitos/corrupção ou deslegitimação institucional.
Responda APENAS com JSON:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO|LIXO|SUSPEITO",
  "confianca_ia": float,
  "analise_pericial": "Motivo rápido (sem usar a palavra crime)"
}
IMPORTANTE: Se houver QUALQUER sinal de ataque ou hostilidade real, marque como "SUSPEITO" para perícia posterior.
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
        import httpx
        self.ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            max_retries=0,
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(timeout=120.0, connect=30.0))
        )
        self.mistral_client = AsyncOpenAI(
            api_key=os.getenv("MISTRAL_API_KEY") or "dummy-mistral-key",
            base_url="https://api.mistral.ai/v1",
            max_retries=0
        )

        _maritaca_key = os.getenv("MARITACA_API_KEY", "").strip()
        self.maritaca_client = AsyncOpenAI(
            api_key=_maritaca_key or "dummy-maritaca-key",
            base_url="https://chat.maritaca.ai/api",
            max_retries=0
        ) if _maritaca_key else None

        finetuned_model = os.getenv('FINETUNED_MODEL_NAME', "open-mistral-nemo")

        self.providers = [
            {"name": "ollama", "client": self.ollama_client, "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b"), "timeout": 120.0, "cooldown_until": 0.0, "is_async_openai": True},
            {"name": "mistral", "client": self.mistral_client, "model": finetuned_model, "timeout": 30.0, "cooldown_until": 0.0, "is_async_openai": True},
        ]

        # Adiciona maritaca APENAS se a chave real estiver configurada
        if _maritaca_key:
            self.providers.append(
                {"name": "maritaca", "client": self.maritaca_client, "model": "sabia-4", "timeout": 20.0, "cooldown_until": 0.0, "is_async_openai": True}
            )
            logger.info("[AI] Maritaca ativada com chave configurada.")
        else:
            logger.info("[AI] Maritaca desativada (MARITACA_API_KEY não configurada).")

        
        try:
            from core.config import FALLBACK_PROVIDERS
            for prov in FALLBACK_PROVIDERS:
                self.providers.append({
                    "name": prov["name"],
                    "model": prov.get("model", ""),
                    "timeout": 45.0,
                    "cooldown_until": 0.0,
                    "is_async_openai": False,
                })
        except Exception as e:
            logger.warning(f"[AI] Falha ao injetar FALLBACK_PROVIDERS: {e}")

        self.consecutive_failures: Dict[str, int] = {}
        self.fallback_llm = None
        
        # Cache de I/O em memória
        self._prompt_cache = {"enriched_local": None, "enriched_cloud": None}
        self.refresh_prompt_cache()

    def refresh_prompt_cache(self) -> None:
        """Recarrega arquivos pesados (MD/JSON) do disco e popula o cache de prompts enriquecidos."""
        self._prompt_cache["enriched_local"] = self._build_enrichment(is_local=True)
        self._prompt_cache["enriched_cloud"] = self._build_enrichment(is_local=False)
        logger.debug("[AI] Cache de prompts enriquecidos recarregado com sucesso.")

    def _build_enrichment(self, is_local: bool) -> str:
        """Gera o prompt do zero combinando SYSTEM_PROMPT, PADRONIZACAO e dataset ouro."""
        base_prompt = LOCAL_SYSTEM_PROMPT if is_local else SYSTEM_PROMPT
        
        # Para modelos locais (Ollama), evitamos o bloat do prompt para não estourar contexto (ReadTimeout/Error 500)
        if is_local:
            enrichment = "\n\n--- DIRETRIZES ESSENCIAIS (TRIAGEM LOCAL) ---\n"
            enrichment += "- Foque em detectar INSULTOS, AMEAÇAS e ACUSAÇÕES GRAVES.\n"
            enrichment += "- Se houver hostilidade clara, marque como SUSPEITO.\n"
            enrichment += "- Críticas normais e slogas são NEUTRO.\n"
            return base_prompt + enrichment

        enrichment = "\n\n--- PADRONIZACAO LINGUÍSTICA ANALITICA (MD) ---\n"
        if os.path.exists(MD_PATH):
            try:
                with open(MD_PATH, "r", encoding="utf-8") as f:
                    enrichment += f.read() + "\n"
            except Exception as e:
                logger.warning(f"[AI] Erro ao ler {MD_PATH}: {e}")
        else:
            enrichment += "(Arquivo de Padronização não encontrado)\n"

        if os.path.exists(CUSTOM_RULES_PATH):
            try:
                with open(CUSTOM_RULES_PATH, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                enrichment += "\n--- DIRETRIZES ADICIONAIS DE PESQUISA (PASA EXTRA) ---\n"
                if "additional_rules" in rules and rules["additional_rules"]:
                    enrichment += "Regras Adicionais de Classificação:\n" + "\n".join(f"- {r}" for r in rules["additional_rules"]) + "\n"
                if "mitigate_false_positives" in rules and rules["mitigate_false_positives"]:
                    enrichment += "Blindagem Extra contra Falsos Positivos:\n" + "\n".join(f"- {r}" for r in rules["mitigate_false_positives"]) + "\n"
                if "custom_keywords" in rules and rules["custom_keywords"]:
                    enrichment += "Dicionário Léxico Customizado por Categoria:\n" + "\n".join(f"- Categoria {cat}: {', '.join(kw)}" for cat, kw in rules["custom_keywords"].items()) + "\n"
            except Exception as e:
                logger.warning(f"[AI] Erro ao carregar {CUSTOM_RULES_PATH}: {e}")

        if not is_local and os.path.exists(GOLD_DATASET_PATH):
            try:
                with open(GOLD_DATASET_PATH, "r", encoding="utf-8") as f:
                    gold_data = json.load(f)
                if isinstance(gold_data, list) and gold_data:
                    examples = [f"- Texto: \"{str(i.get('text', ''))[:240]}\" -> Categoria: {str(i.get('label', '')).upper()}" for i in gold_data[-10:] if i.get("text") and i.get("label")]
                    if examples:
                        enrichment += "\n\n--- PADRÃO OURO AUDITADO ---\nUse estes exemplos como calibração:\n" + "\n".join(examples) + "\n"
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
        """Gira a fila unificada transferindo o provider selecionado para o final."""
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            self.providers.append(prov)
            logger.debug(f"🔄 [AI] Provedor '{name}' rotacionado. Motivo: {reason}")

    def _remove_provider(self, name: str, reason: str = "") -> None:
        """Remove permanentemente o provedor da fila unificada."""
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            logger.warning(f"🚨 [AI] Provedor '{name}' REMOVIDO permanentemente. {reason}")

    def _handle_provider_error(self, provider: Dict[str, Any], exception: Exception) -> bool:
        """
        Processa exceções de APIs e aplica penalidades na fila de providers.
        Retorna `True` se o provider foi removido, `False` se foi rotacionado com cooldown.
        """
        import httpx
        name = provider["name"]
        
        status_code = getattr(exception, "status_code", None)
        if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
            status_code = exception.response.status_code
            
        if name == "ollama" and isinstance(exception, (httpx.ConnectError, httpx.ConnectTimeout)):
            status_code = 503
            
        self.consecutive_failures[name] = self.consecutive_failures.get(name, 0) + 1
        ai_circuit_breaker.record_failure(name, status_code if status_code else 500)
        
        if status_code in [400, 401, 402, 403, 404]:
            self._remove_provider(name, f"Erro Crítico de Acesso/Cota/Bad Request ({status_code})")
            return True
            
        if status_code == 429:
            provider["cooldown_until"] = time.time() + 60.0
            penalty_desc = "60s (Rate Limit 429)"
        else:
            provider["cooldown_until"] = time.time() + 30.0
            penalty_desc = f"30s (Erro {status_code or 'desconhecido'})"
            
        self._rotate_provider(name, f"Falha temporária - {penalty_desc} - {str(exception)[:100]}")
        return False

    async def _execute_provider_call(self, provider: Dict[str, Any], final_system_prompt: str, user_content: str, response_format: str) -> str:
        """Encapsula o dispatch do cliente (AsyncOpenAI vs FallbackLLM)."""
        name = provider["name"]
        
        if provider.get("is_async_openai", False):
            response = await provider["client"].chat.completions.create(
                model=provider["model"],
                messages=[{"role": "system", "content": final_system_prompt}, {"role": "user", "content": user_content}],
                response_format={"type": response_format},
                temperature=0.0,
                timeout=provider.get("timeout", 15.0)
            )
            return response.choices[0].message.content
        else:
            if self.fallback_llm is None:
                from core.fallback_llm import FallbackLLM
                self.fallback_llm = FallbackLLM()
            
            fallback_text = f"{final_system_prompt}\n\nUser: \"{user_content}\"\n\nResponda estritamente no formato exigido."
            return await asyncio.to_thread(self.fallback_llm.classify, fallback_text, name)

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        return await self.classify_text(text, comment_id)

    async def chat_completion(self, prompt: str, system_prompt: str = "Você é um assistente técnico...", response_format: str = "json_object") -> Optional[Dict[str, Any]]:
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
                
                self._rotate_provider(name, "Sucesso (cooldown 1s)")
                active_providers.remove(provider)
                active_providers.append(provider)
                
                return json.loads(content) if response_format == "json_object" else {"content": content}
                
            except Exception as e:
                logger.warning(f"[AI] Falha no provider '{name}' em chat_completion: {e}")
                was_removed = self._handle_provider_error(provider, e)
                active_providers.remove(provider)
                if not was_removed:
                    active_providers.append(provider)
                continue
                
        return None

    async def classify_text(self, text: str, comment_id: str = "N/A", trace_id: str = None) -> Dict[str, Any]:
        if not isinstance(text, str):
            text = str(text or "")
        text = text.strip()
        if not text:
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Texto vazio.", "name": "guard"}
        if len(text) > 8000:
            text = text[:8000]

        from core.lexical_filter import lexical_filter
        if lexical_filter.is_junk(text):
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Filtro léxico.", "name": "lexical"}

        max_attempts = len(self.providers)
        
        for _ in range(max_attempts):
            provider = self.providers[0]
            name = provider["name"]

            if not ai_circuit_breaker.can_execute(name):
                self._rotate_provider(name, "Circuito Aberto")
                continue
                
            now = time.time()
            if now < provider.get("cooldown_until", 0.0):
                await asyncio.sleep(provider["cooldown_until"] - now)

            try:
                is_local = name == "ollama"
                final_system_prompt = self._get_system_prompt(is_local)
                user_content = f"Texto: \"{text}\""
                
                content = await self._execute_provider_call(provider, final_system_prompt, user_content, "json_object")
                res = self._parse_json_response(content)
                res["name"] = name
                
                provider["cooldown_until"] = time.time() + 1.0
                self.consecutive_failures[name] = 0
                ai_circuit_breaker.record_success(name)
                
                self._rotate_provider(name, "Sucesso (cooldown 1s)")
                
                trace_log = f" | Trace: {trace_id}" if trace_id else ""
                logger.info(f"✅ [AI] {name.upper():<15} | ID: {comment_id:<36}{trace_log} | {res['categoria_ia']:<20}")
                return res

            except Exception as e:
                logger.debug("[AI] Falha unificada no provider '%s' para comment_id=%s: %s", name, comment_id, e)
                self._handle_provider_error(provider, e)
                continue

        logger.error(f"❌ [AI] Todos os provedores falharam para o ID {comment_id}. Colapso temporário.")
        return {
            "is_hate": False, 
            "categoria_ia": "ERRO", 
            "confianca_ia": 0.5, 
            "analise_pericial": "Todos os provedores da fila unificada falharam.", 
            "name": "system_failure"
        }

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
                except Exception:
                    pass

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

        is_hate = bool(parsed.get("is_hate", False))
        if category in {"NEUTRO", "LIXO"}:
            is_hate = False

        analise = str(parsed.get("analise_pericial", "")).strip() or "Sem análise."
        return {"is_hate": is_hate, "categoria_ia": category, "confianca_ia": confidence, "analise_pericial": analise}

    async def run_batch_classification(self, limit: int = 50) -> int:
        """Busca comentários não processados no banco e executa a classificação."""
        try:
            from core.db import db_client
            res = db_client.client.table('comentarios').select('id, texto_bruto, trace_id').eq('processado_ia', False).limit(limit).execute()
            items = res.data or []
            count = 0
            for item in items:
                try:
                    res_ia = await self.classify_text(item["texto_bruto"], item["id"], trace_id=item.get("trace_id"))
                    if res_ia and res_ia.get("categoria_ia") != "ERRO":
                        engine_name = res_ia.get("name", "unknown").upper()
                        analise = f"[{engine_name}] {res_ia.get('analise_pericial', '')}"
                        db_client.client.table('comentarios').update({
                            "categoria_ia": res_ia["categoria_ia"], "confianca_ia": res_ia["confianca_ia"], "is_hate": res_ia["is_hate"], "analise_pericial": analise, "processado_ia": True
                        }).eq("id", item["id"]).execute()
                        count += 1
                    
                    # PASA v88.2 - Cadência Constante (Persistência sobre Velocidade)
                    # Introduz delay para evitar picos e respeitar limites de IA a longo prazo
                    await asyncio.sleep(1.0)
                except Exception as e:
                    if "Colapso" in str(e):
                        logger.error("🛑 [AI] Colapso detectado nas APIs. Abortando lote.")
                        raise e 
            return count
        except Exception as e:
            raise e 

    async def run_batch_reanalysis(self, limit: int = 20, confidence_threshold: float = 0.6) -> int:
        """Busca registros já processados mas com baixa confiança para re-análise profunda."""
        try:
            from core.db import db_client
            res = db_client.client.table('comentarios').select('id, texto_bruto, trace_id').eq('processado_ia', True).lt('confianca_ia', confidence_threshold).not_.eq('categoria_ia', 'ERRO').order('data_coleta', desc=True).limit(limit).execute()
            items = res.data or []
            count = 0
            
            ollama_prov = next((p for p in self.providers if p["name"] == "ollama"), None)
            if ollama_prov: self.providers.remove(ollama_prov)

            try:
                for item in items:
                    try:
                        res_ia = await self.classify_text(item["texto_bruto"], item["id"], trace_id=item.get("trace_id"))
                        if res_ia and res_ia.get("categoria_ia") != "ERRO":
                            engine_name = res_ia.get("name", "unknown").upper()
                            analise = f"[RE-ANÁLISE:{engine_name}] {res_ia.get('analise_pericial', '')}"
                            db_client.client.table('comentarios').update({
                                "categoria_ia": res_ia["categoria_ia"], "confianca_ia": res_ia["confianca_ia"], "is_hate": res_ia["is_hate"], "analise_pericial": analise
                            }).eq("id", item["id"]).execute()
                            count += 1
                        
                        # PASA v88.2 - Cadência Constante (Persistência sobre Velocidade)
                        await asyncio.sleep(1.0)
                    except Exception as e:
                        if "Colapso" in str(e): break
            finally:
                if ollama_prov: self.providers.append(ollama_prov)
                
            return count
        except Exception as e:
            raise e

    async def push_custom_rules_to_providers(self) -> None:
        pass

ai_service = AIService()
