"""
PASA v52.3 - AI Service: Motor de Inteligência Resiliente (Hybrid Cascade)
Roteamento dinâmico: Ollama (Local) -> Mistral -> Groq -> OpenRouter.
"""
import os
import json
import logging
import traceback
import re
import codecs
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

logger = logging.getLogger("AIService")

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
GOLD_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "classifier_gold_dataset.json",
)
# MCA v2.2 Protocol - Calibragem Forense Crítica (v85.11)
SYSTEM_PROMPT = """Você é um perito em Linguística Forense Digital especializado em ataques coordenados e hostilidade política.
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

# Prompt de Triagem Local - Ultra Rápido (v85.11)
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
            try: return codecs.decode(match.group(0), 'unicode-escape')
            except: return match.group(0)
        pattern = r'\\u[dD][89abAB][0-9a-fA-F]{2}\\u[dD][cdefCDEF][0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}'
        decoded = re.sub(pattern, decode_escapes, s)
        return decoded.encode('utf-8', errors='replace').decode('utf-8')
    except:
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
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=45.0, connect=1.5)
            )
        )
        self.mistral_client = AsyncOpenAI(
            api_key=os.getenv("MISTRAL_API_KEY") or "dummy-mistral-key",
            base_url="https://api.mistral.ai/v1",
            max_retries=0
        )
        self.groq_client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY") or "dummy-groq-key",
            base_url="https://api.groq.com/openai/v1",
            max_retries=0
        )
        self.openrouter_client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY") or "dummy-openrouter-key",
            base_url="https://openrouter.ai/api/v1",
            max_retries=0
        )

        finetuned_model = os.getenv('FINETUNED_MODEL_NAME')
        mistral_model = finetuned_model if finetuned_model else "open-mistral-nemo"

        # Tenta Qwen2.5 se disponível no Ollama, senão Gemma:2b
        self.providers = [
            {"name": "ollama", "client": self.ollama_client, "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b"), "timeout": 45.0},
            {"name": "mistral", "client": self.mistral_client, "model": mistral_model, "timeout": 15.0},
            {"name": "groq", "client": self.groq_client, "model": "llama-3.3-70b-versatile", "timeout": 10.0},
            {"name": "openrouter", "client": self.openrouter_client, "model": "openrouter/free", "timeout": 20.0},
        ]
        self.consecutive_failures: Dict[str, int] = {}
        self.fallback_llm = None

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        return await self.classify_text(text, comment_id)

    async def chat_completion(self, prompt: str, system_prompt: str = "Você é um assistente técnico especializado no sistema Sentinela.", response_format: str = "json_object") -> Optional[Dict[str, Any]]:
        providers = [p for p in self.providers if p["name"] not in ["ollama"]]
        if not providers: providers = self.providers
        for provider in providers:
            if not ai_circuit_breaker.can_execute(provider["name"]): continue
            try:
                response = await provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                    response_format={"type": response_format},
                    temperature=0.0,
                    timeout=20.0
                )
                content = response.choices[0].message.content
                return json.loads(content) if response_format == "json_object" else {"content": content}
            except: continue
        return None

    async def classify_text(self, text: str, comment_id: str = "N/A", trace_id: str = None) -> Dict[str, Any]:
        from core.lexical_filter import lexical_filter
        if lexical_filter.is_junk(text):
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Filtro léxico.", "name": "lexical"}

        local_result = None
        # Cria cópia estática para evitar bugs ao alterar a lista self.providers concorrentemente/durante o loop
        active_providers = list(self.providers)
        
        # CAMADA 1: FILTRAGEM LOCAL (OLLAMA)
        for provider in active_providers:
            if provider["name"] not in ["ollama"] or not ai_circuit_breaker.can_execute(provider["name"]):
                continue
            try:
                res = await self._call_provider(provider, text, comment_id)
                if res:
                    local_result = res
                    # Se for Neutro ou Lixo com confiança decente, encerra aqui (Custo Zero)
                    if res.get("confianca_ia", 0) >= 0.7 and res.get("categoria_ia") in ["NEUTRO", "LIXO"]:
                        trace_log = f" | Trace: {trace_id}" if trace_id else ""
                        logger.info(f"🟢 [AI] {provider['name'].upper():<10} | ID: {comment_id:<36}{trace_log} | {res['categoria_ia']:<20} | (Triagem Local)")
                        return res
                    continue
            except: continue

        # CAMADA 2: PERÍCIA CLOUD (MISTRAL/GROQ) - Só se local for SUSPEITO ou incerto
        for provider in active_providers:
            if provider["name"] in ["ollama"] or not ai_circuit_breaker.can_execute(provider["name"]):
                continue
            try:
                res = await self._call_provider(provider, text, comment_id)
                if res:
                    trace_log = f" | Trace: {trace_id}" if trace_id else ""
                    logger.info(f"🔍 [AI] {provider['name'].upper():<10} | ID: {comment_id:<36}{trace_log} | {res['categoria_ia']:<20} | (Refinado)")
                    return res
            except: continue

        # CAMADA 3: FALLBACK PROFUNDO (FALLBACK_LLM)
        try:
            if self.fallback_llm is None:
                from core.fallback_llm import FallbackLLM
                self.fallback_llm = FallbackLLM()
            logger.warning(f"🚨 [AI] ID: {comment_id:<36} | Todos os provedores primários/cloud estão indisponíveis. Acionando FallbackLLM...")
            
            # Como FallbackLLM não aceita system_prompt, injetamos a regra no próprio texto
            fallback_text = f"{text}\n\nResponda APENAS com um JSON estrito no formato: {{\"is_hate\": boolean, \"categoria_ia\": \"NEUTRO|LIXO|SUSPEITO|ERRO\", \"confianca_ia\": float, \"analise_pericial\": \"motivo\"}}"
            raw_response = self.fallback_llm.classify(fallback_text)
            
            res = self._parse_json_response(raw_response)
            res["name"] = "fallback_llm"
            trace_log = f" | Trace: {trace_id}" if trace_id else ""
            logger.info(f"🟢 [AI] FALLBACK_LLM | ID: {comment_id:<36}{trace_log} | {res.get('categoria_ia', 'ERRO'):<20} | (Recuperação de Desastre)")
            return res
        except Exception as e:
            logger.error(f"❌ [AI] FallbackLLM falhou após colapso dos primários: {e}")
            raise RuntimeError("Colapso total das APIs de Inteligência Artificial")

    def _enrich_prompt(self, is_local: bool) -> str:
        base_prompt = LOCAL_SYSTEM_PROMPT if is_local else SYSTEM_PROMPT
        # Busca config/custom_rules.json na raiz do projeto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "custom_rules.json")
        
        if not os.path.exists(config_path):
            config_path = "config/custom_rules.json"
            
        if not os.path.exists(config_path):
            return base_prompt

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                rules = json.load(f)
            
            enrichment = "\n\n--- DIRETRIZES ADICIONAIS DE PESQUISA (PASA EXTRA) ---\n"
            has_enrichment = False
            
            if "additional_rules" in rules and rules["additional_rules"]:
                enrichment += "Regras Adicionais de Classificação:\n"
                for r in rules["additional_rules"]:
                    enrichment += f"- {r}\n"
                has_enrichment = True
                
            if "mitigate_false_positives" in rules and rules["mitigate_false_positives"]:
                enrichment += "Blindagem Extra contra Falsos Positivos:\n"
                for r in rules["mitigate_false_positives"]:
                    enrichment += f"- {r}\n"
                has_enrichment = True
                
            if "custom_keywords" in rules and rules["custom_keywords"]:
                enrichment += "Dicionário Léxico Customizado por Categoria:\n"
                for cat, kw_list in rules["custom_keywords"].items():
                    enrichment += f"- Categoria {cat}: {', '.join(kw_list)}\n"
                has_enrichment = True
                
            if has_enrichment:
                if "--- FORMATO DE RESPOSTA (JSON APENAS) ---" in base_prompt:
                    parts = base_prompt.split("--- FORMATO DE RESPOSTA (JSON APENAS) ---")
                    return parts[0] + enrichment + "\n--- FORMATO DE RESPOSTA (JSON APENAS) ---" + parts[1]
                else:
                    return base_prompt + enrichment
        except Exception as e:
            logger.warning(f"Falha ao carregar regras customizadas em {config_path}: {e}")

        gold_enrichment = self._build_gold_dataset_enrichment(is_local)
        if gold_enrichment:
            if "--- FORMATO DE RESPOSTA (JSON APENAS) ---" in base_prompt:
                parts = base_prompt.split("--- FORMATO DE RESPOSTA (JSON APENAS) ---")
                return parts[0] + gold_enrichment + "\n--- FORMATO DE RESPOSTA (JSON APENAS) ---" + parts[1]
            return base_prompt + gold_enrichment

        return base_prompt

    def _build_gold_dataset_enrichment(self, is_local: bool) -> str:
        if is_local or not os.path.exists(GOLD_DATASET_PATH):
            return ""

        try:
            with open(GOLD_DATASET_PATH, "r", encoding="utf-8") as f:
                gold_data = json.load(f)
        except Exception as e:
            logger.warning(f"Falha ao carregar padrão ouro em {GOLD_DATASET_PATH}: {e}")
            return ""

        if not isinstance(gold_data, list) or not gold_data:
            return ""

        examples = []
        for item in gold_data[-10:]:
            text = str(item.get("text", "")).strip()
            label = str(item.get("label", "")).strip().upper()
            if text and label:
                examples.append(f"- Texto: \"{text[:240]}\" -> Categoria: {label}")

        if not examples:
            return ""

        return "\n\n--- PADRÃO OURO AUDITADO ---\nUse estes exemplos auditados como referência adicional de calibração:\n" + "\n".join(examples) + "\n"

    async def _call_provider(self, provider: Dict[str, Any], text: str, comment_id: str) -> Optional[Dict[str, Any]]:
        name = provider["name"]
        is_local = name in ["ollama"]
        system_prompt = self._enrich_prompt(is_local)
        try:
            response = await provider["client"].chat.completions.create(
                model=provider["model"],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Texto: \"{text}\""}],
                response_format={"type": "json_object"},
                temperature=0.0,
                timeout=provider.get("timeout", 15.0)
            )
            result = self._parse_json_response(response.choices[0].message.content)
            result["name"] = name
            self.consecutive_failures[name] = 0
            ai_circuit_breaker.record_success(name)
            return result
        except Exception as e:
            import httpx
            import openai
            
            is_local = name in ["ollama"]
            status_code = None
            
            if hasattr(e, "status_code"):
                status_code = getattr(e, "status_code")
            elif hasattr(e, "code"):
                try:
                    status_code = int(getattr(e, "code"))
                except:
                    pass

            is_connect_error = isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout))
            is_read_timeout = isinstance(e, (httpx.ReadTimeout, openai.APITimeoutError)) or "timeout" in str(e).lower()
            
            if is_local and is_connect_error:
                status_code = 503
                logger.warning(f"⚠️ [AI] Provedor local '{name}' indisponível/offline (falha de conexão). Abrindo disjuntor imediatamente.")
            
            ai_circuit_breaker.record_failure(name, status_code=status_code)
            
            should_remove = False
            
            if is_local:
                if is_connect_error:
                    self.consecutive_failures[name] = self.consecutive_failures.get(name, 0) + 1
                    if self.consecutive_failures[name] >= 3:
                        should_remove = True
            else:
                if status_code in [401, 403]:
                    should_remove = True
                    logger.error(f"❌ [AI] Provedor Cloud '{name}' retornou erro de credenciais ({status_code}).")

            if should_remove:
                self._remove_provider(name, f"Erro grave ou falhas consecutivas (status {status_code})")
            else:
                self._rotate_provider(name, "Falha temporária")
            
            return None

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except:
            # Fallback regex para JSONs malformados
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try: return json.loads(match.group(0))
                except: pass
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 0.5, "analise_pericial": "Erro parser."}

    def _rotate_provider(self, name: str, reason: str = "") -> None:
        """Move provider to end of rotation queue, preserving order."""
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            self.providers.append(prov)
            logger.info(f"🔄 [AI] Provedor '{name}' rotacionado. {reason}")

    def _remove_provider(self, name: str, reason: str = "") -> None:
        """Remove provider permanently from active list."""
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            logger.warning(f"🚨 [AI] Provedor '{name}' REMOVIDO permanentemente. {reason}")

    async def run_batch_classification(self, limit: int = 50) -> int:
        """Busca comentários não processados no banco e executa a classificação."""
        try:
            from core.db import db_client
            res = db_client.client.table('comentarios')\
                .select('id, texto_bruto, trace_id')\
                .eq('processado_ia', False)\
                .limit(limit).execute()
            
            items = res.data or []
            if not items: return 0
            
            count = 0
            for item in items:
                try:
                    res_ia = await self.classify_text(item["texto_bruto"], item["id"], trace_id=item.get("trace_id"))
                    if res_ia:
                        engine_name = res_ia.get("name", "unknown").upper()
                        analise = f"[{engine_name}] {res_ia.get('analise_pericial', '')}"
                        db_client.client.table('comentarios').update({
                            "categoria_ia": res_ia["categoria_ia"],
                            "confianca_ia": res_ia["confianca_ia"],
                            "is_hate": res_ia["is_hate"],
                            "analise_pericial": analise,
                            "processado_ia": True
                        }).eq("id", item["id"]).execute()
                        count += 1
                except Exception as e:
                    if "Colapso total" in str(e):
                        logger.error("🛑 [AI] Colapso detectado nas APIs. Abortando lote para preservar fila.")
                        raise e # Repassa para o Worker entrar em modo de falha (circuit breaker)
                    continue
            return count
        except Exception as e:
            logger.error(f"Error in batch classification: {e}")
            raise e # Repassa para o Worker registrar falha e não mascarar erro

    async def run_batch_reanalysis(self, limit: int = 20, confidence_threshold: float = 0.6) -> int:
        """
        Busca registros já processados mas com baixa confiança para re-análise profunda (PASA v85.12).
        Utiliza apenas modelos Cloud para o refinamento.
        """
        try:
            from core.db import db_client
            # Busca itens com confiança abaixo do threshold
            res = db_client.client.table('comentarios')\
                .select('id, texto_bruto, trace_id')\
                .eq('processado_ia', True)\
                .lt('confianca_ia', confidence_threshold)\
                .not_.eq('categoria_ia', 'ERRO')\
                .order('data_coleta', desc=True)\
                .limit(limit).execute()
            
            items = res.data or []
            if not items: return 0
            
            count = 0
            for item in items:
                # Força uso de modelos Cloud para re-análise
                original_providers = list(self.providers)
                self.providers = [p for p in original_providers if p["name"] not in ["ollama"]]
                
                try:
                    res_ia = await self.classify_text(item["texto_bruto"], item["id"], trace_id=item.get("trace_id"))
                    # PASA v86.10: Se a re-análise falhou ou deu ERRO, mantemos o resultado anterior
                    if res_ia and res_ia.get("categoria_ia") != "ERRO":
                        engine_name = res_ia.get("name", "unknown").upper()
                        analise = f"[RE-ANÁLISE:{engine_name}] {res_ia.get('analise_pericial', '')}"
                        db_client.client.table('comentarios').update({
                            "categoria_ia": res_ia["categoria_ia"],
                            "confianca_ia": res_ia["confianca_ia"],
                            "is_hate": res_ia["is_hate"],
                            "analise_pericial": analise
                        }).eq("id", item["id"]).execute()
                        count += 1
                except Exception as e:
                    if "Colapso total" in str(e):
                        logger.error("🛑 [AI] Colapso detectado nas APIs durante re-análise. Abortando lote.")
                        raise e
                    continue
                finally:
                    self.providers = original_providers
                    
            return count
        except Exception as e:
            logger.error(f"Error in batch reanalysis: {e}")
            raise e

ai_service = AIService()
