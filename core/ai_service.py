"""
PASA v52.3 - AI Service: Motor de Inteligência Resiliente (Hybrid Cascade)
Roteamento dinâmico: LiteRT (Local) -> Ollama (Local) -> Mistral -> Groq -> OpenRouter.
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
# MCA v2.2 Protocol - Calibragem Forense Crítica (v85.11)
SYSTEM_PROMPT = """Você é um perito em Linguística Forense Digital especializado em ataques coordenados e hostilidade política.
Sua missão é classificar comentários com realismo absoluto, seguindo a Metodologia de Classificação de Ataques (MCA v2.2) e as Diretrizes do Protocolo PASA v16.4.

--- REGRAS DE OURO ---
1. REALISMO: Não ignore ataques velados, ironias destrutivas ou acusações de corrupção/crime.
2. DISTINÇÃO: Crítica política legítima foca em IDEIAS. Ataques focam em PESSOAS ou INSTITUIÇÕES.
3. COMUNICAÇÃO: Você é um sistema de INFORMAÇÃO. Se detectar uma imputação de crime, você NÃO DEVE usar a palavra "crime" na sua classificação ou análise. Você deve rotular como dano à reputação.
4. IDIOMA: Sua resposta (incluindo a analise_pericial) deve ser 100% em Português Brasileiro (pt-BR).

--- CATEGORIZAÇÃO (MCA v2.2) ---
Se o comentário for classificado como hostil (is_hate: true), escolha obrigatoriamente uma das chaves exatas abaixo para "categoria_ia":
- ODIO_IDENTITARIO: Ataques baseados em raça, religião, orientação sexual, misoginia ou XENOFOBIA/REGIONALISMO.
- VIOLENCIA_GENERO: Ofensas focadas na condição feminina.
- AMEACA: Incitação a dano físico, violência física ou morte.
- INSULTO_AD_HOMINEM: Desumanização, baixo calão, ataques à honra, moral, aparência ou competência.
- ATAQUE_INSTITUCIONAL: Deslegitimação de órgãos de Estado, governos ou do sistema democrático.
- DANO_REPUTACIONAL_GRAVE: Imputação direta de atos ilícitos, corrupção, roubo ou infrações graves. (IMPORTANTE: Use esta categoria para qualquer acusação que, na prática, seria um crime, mas use APENAS este nome de categoria).

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
  "categoria_ia": "ODIO_IDENTITARIO|VIOLENCIA_GENERO|AMEACA|INSULTO_AD_HOMINEM|ATAQUE_INSTITUCIONAL|DANO_REPUTACIONAL_GRAVE|NEUTRO", 
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
        self.litert_client = AsyncOpenAI(
            api_key="litert",
            base_url=os.getenv("LITERT_BASE_URL", "http://localhost:9379/v1")
        )
        self.ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        )
        self.mistral_client = AsyncOpenAI(
            api_key=os.getenv("MISTRAL_API_KEY") or "dummy-mistral-key",
            base_url="https://api.mistral.ai/v1"
        )
        self.groq_client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY") or "dummy-groq-key",
            base_url="https://api.groq.com/openai/v1"
        )
        self.openrouter_client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY") or "dummy-openrouter-key",
            base_url="https://openrouter.ai/api/v1"
        )

        finetuned_model = os.getenv('FINETUNED_MODEL_NAME')
        mistral_model = finetuned_model if finetuned_model else "open-mistral-nemo"

        # Tenta Qwen2.5 se disponível no Ollama, senão Gemma:2b
        self.providers = [
            {"name": "litert", "client": self.litert_client, "model": "gemma3-1b-it", "timeout": 10.0},
            {"name": "ollama", "client": self.ollama_client, "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b"), "timeout": 45.0},
            {"name": "mistral", "client": self.mistral_client, "model": mistral_model, "timeout": 15.0},
            {"name": "groq", "client": self.groq_client, "model": "llama-3.3-70b-versatile", "timeout": 10.0},
            {"name": "openrouter", "client": self.openrouter_client, "model": "openrouter/free", "timeout": 20.0},
        ]

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        return await self.classify_text(text, comment_id)

    async def chat_completion(self, prompt: str, system_prompt: str = "Você é um assistente técnico especializado no sistema Sentinela.", response_format: str = "json_object") -> Optional[Dict[str, Any]]:
        providers = [p for p in self.providers if p["name"] not in ["litert", "ollama"]]
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

    async def classify_text(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        from core.lexical_filter import lexical_filter
        if lexical_filter.is_junk(text):
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Filtro léxico."}

        self.providers.sort(key=lambda p: ai_circuit_breaker.failures.get(p["name"], 0))
        local_result = None
        
        # CAMADA 1: FILTRAGEM LOCAL (OLLAMA/LITERT)
        for provider in self.providers:
            if provider["name"] not in ["litert", "ollama"] or not ai_circuit_breaker.can_execute(provider["name"]):
                continue
            try:
                res = await self._call_provider(provider, text, comment_id)
                if res:
                    local_result = res
                    # Se for Neutro ou Lixo com confiança decente, encerra aqui (Custo Zero)
                    if res.get("confianca_ia", 0) >= 0.7 and res.get("categoria_ia") in ["NEUTRO", "LIXO"]:
                        logger.info(f"🟢 [AI] {provider['name'].upper():<10} | ID: {comment_id:<36} | {res['categoria_ia']:<20} | (Triagem Local)")
                        return res
                    break
            except: continue

        # CAMADA 2: PERÍCIA CLOUD (MISTRAL/GROQ) - Só se local for SUSPEITO ou incerto
        for provider in self.providers:
            if provider["name"] in ["litert", "ollama"] or not ai_circuit_breaker.can_execute(provider["name"]):
                continue
            try:
                res = await self._call_provider(provider, text, comment_id)
                if res:
                    logger.info(f"🔍 [AI] {provider['name'].upper():<10} | ID: {comment_id:<36} | {res['categoria_ia']:<20} | (Refinado)")
                    return res
            except: continue

        return local_result or {"is_hate": False, "categoria_ia": "ERRO", "confianca_ia": 0.0, "analise_pericial": "Falha total."}

    async def _call_provider(self, provider: Dict[str, Any], text: str, comment_id: str) -> Optional[Dict[str, Any]]:
        name = provider["name"]
        is_local = name in ["litert", "ollama"]
        system_prompt = LOCAL_SYSTEM_PROMPT if is_local else SYSTEM_PROMPT
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
            ai_circuit_breaker.record_success(name)
            return result
        except Exception as e:
            ai_circuit_breaker.record_failure(name)
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

    async def run_batch_reanalysis(self, limit: int = 20, confidence_threshold: float = 0.6) -> int:
        """
        Busca registros já processados mas com baixa confiança para re-análise profunda (PASA v85.12).
        Utiliza apenas modelos Cloud para o refinamento.
        """
        try:
            from core.db import db_client
            # Busca itens com confiança abaixo do threshold
            res = db_client.client.table('comentarios')\
                .select('id, texto_bruto')\
                .eq('processado_ia', True)\
                .lt('confianca_ia', confidence_threshold)\
                .order('data_coleta', desc=True)\
                .limit(limit).execute()
            
            items = res.data or []
            if not items: return 0
            
            count = 0
            for item in items:
                # Força uso de modelos Cloud para re-análise
                # Remove modelos locais da lista temporariamente para esta chamada
                original_providers = self.providers
                self.providers = [p for p in original_providers if p["name"] not in ["litert", "ollama"]]
                
                try:
                    res_ia = await self.classify_text(item["texto_bruto"], item["id"])
                    if res_ia and res_ia.get("confianca_ia", 0) > 0.1:
                        db_client.client.table('comentarios').update({
                            "categoria_ia": res_ia["categoria_ia"],
                            "confianca_ia": res_ia["confianca_ia"],
                            "is_hate": res_ia["is_hate"],
                            "analise_pericial": f"[RE-ANÁLISE] {res_ia.get('analise_pericial', '')}"
                        }).eq("id", item["id"]).execute()
                        count += 1
                except: continue
                finally:
                    self.providers = original_providers
                    
            return count
        except Exception as e:
            logger.error(f"Error in batch reanalysis: {e}")
            return 0

ai_service = AIService()
