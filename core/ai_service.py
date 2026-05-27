"""
PASA v52.3 - AI Service: Motor de Inteligência Resiliente (Hybrid Cascade)
Roteamento dinâmico: LiteRT (Local) -> Ollama (Local) -> Mistral -> Groq -> OpenRouter.
"""
import os
import json
import logging
logger = logging.getLogger("AIService")
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
# MCA v2.2 Protocol - Calibragem Forense Crítica (v84.0)
SYSTEM_PROMPT = """Você é um perito em Linguística Forense Digital especializado em ataques coordenados e hostilidade política.
Sua missão é classificar comentários com realismo absoluto, seguindo a Metodologia de Classificação de Ataques (MCA v2.2) e as Diretrizes do Protocolo PASA v16.4.

--- REGRAS DE OURO ---
1. REALISMO: Não ignore ataques velados, ironias destrutivas ou acusações de corrupção/crime.
2. DISTINÇÃO: Crítica política legítima foca em IDEIAS. Ataques focam em PESSOAS ou INSTITUIÇÕES.
3. IDIOMA: Sua resposta (incluindo a analise_pericial) deve ser 100% em Português Brasileiro (pt-BR).

--- CATEGORIZAÇÃO (MCA v2.2) ---
Se o comentário for classificado como hostil (is_hate: true), escolha obrigatoriamente uma das chaves exatas abaixo para "categoria_ia":
- ODIO_IDENTITARIO: Ataques baseados em raça, religião, orientação sexual, misoginia ou XENOFOBIA/REGIONALISMO (ex: ridicularização de sotaques, uso de identidades regionais como adjetivo pejorativo ou estereótipos de "preguiça").
- VIOLENCIA_GENERO: Ofensas focadas na condição feminina e ataques de gênero contra figuras femininas (ex: "vaca", "puta", "louca").
- AMEACA: Incitação a dano físico, violência física ou morte (ex: "tem que levar tiro", "paredão", "morte aos traidores").
- INSULTO_AD_HOMINEM: Desumanização, baixo calão, ataques à honra, moral, aparência ou competência (ex: "verme", "rato", "lixo", "incompetente", "frouxo", "traidor").
- ATAQUE_INSTITUCIONAL: Deslegitimação de órgãos de Estado, governos ou do sistema democrático (ex: "ditadura da toga", "urnas fraudadas", "juiz comprado").
- RIGOR_CRIMINAL: Imputação direta de crime sem trânsito em julgado ou provas concretas (ex: "ladrão", "traficante", "corrupto", "miliciano").

Se o comentário NÃO for hostil (is_hate: false), a "categoria_ia" deve ser obrigatoriamente:
- NEUTRO: Expressões de engajamento legítimo, slogans, críticas técnicas ou frases protegidas pela Blindagem de Falsos Positivos.

--- BLINDAGEM CONTRA FALSOS POSITIVOS (PROTOCOLO DE DEFESA) ---
Marque como NEUTRO (is_hate: false e categoria_ia: "NEUTRO") os seguintes cenários (NÃO são ódio/hostilidade):
1. ENTUSIASMO / APOIO: Frases de engajamento democrático como "Fulano no Congresso será um presente", "A ousadia vai ocupar o congresso" ou "Vamos pra cima".
2. DEFESA DE MANDATO: Denúncias de "perseguição", "lawfare" ou "investida autoritária" em defesa do alvo monitorado (são opiniões políticas, não ataques institucionais).
3. METÁFORAS DE EMBATE: Termos como "inimigos do povo", "servir de lição" ou "mobilizar nas ruas" no contexto eleitoral/manifestação legítima (não configuram AMEACA).
4. APOIO AGRESSIVO / GÍRIAS: Uso de palavrões ("porra", "caralho") ou gírias ("o brabo", "mito", "papai") em frases de exaltação ao alvo (foco na intenção de apoio, não no vernáculo).

--- FORMATO DE RESPOSTA (JSON APENAS) ---
{
  "is_hate": boolean, 
  "categoria_ia": "ODIO_IDENTITARIO|VIOLENCIA_GENERO|AMEACA|INSULTO_AD_HOMINEM|ATAQUE_INSTITUCIONAL|RIGOR_CRIMINAL|NEUTRO", 
  "confianca_ia": float (0.0 a 1.0),
  "analise_pericial": "Explicação técnica curta e realista do porquê desta classificação."
}

AVISO: Se o comentário contém acusações de crime ou insultos reais, "is_hate" DEVE ser true.
"""

# Prompt de Triagem Local - Ultra Rápido (v84.0)
LOCAL_SYSTEM_PROMPT = """Você é um classificador binário de hostilidade política. 
Analise se o texto contém: insultos reais, ameaças, acusações criminais ou deslegitimação institucional.
Responda APENAS com JSON:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO|LIXO|SUSPEITO",
  "confianca_ia": float,
  "analise_pericial": "Motivo rápido"
}
IMPORTANTE: Se houver QUALQUER sinal de ataque ou hostilidade real, marque como "SUSPEITO" para perícia posterior.
Frases de exaltação com gírias/palavrões ("porra", "caralho"), elogios eleitorais ("ocupar o congresso") ou opiniões legítimas de defesa política devem ser classificadas como "NEUTRO" com alta confiança.
"""

def load_training_context() -> str:
    """Carrega o dataset de treinamento (PDFs de ironia/sarcasmo) como contexto in-prompt (In-Context Learning)."""
    try:
        dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "training", "pasa_training_dataset.jsonl")
        if not os.path.exists(dataset_path):
            return ""
            
        training_text = "\n\n--- BASE DE CONHECIMENTO (TREINAMENTO DE SARCASMO E IRONIA) ---\nUtilize as referências abaixo (extraídas de artigos científicos) para embasar sua detecção de ironia:\n"
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                prompt_text = data.get("prompt", "")
                if "Texto:" in prompt_text:
                    excerpt = prompt_text.split("Texto:")[1].strip()
                    training_text += f"- {excerpt}\n"
                    if len(training_text) > 8000:
                        break
        return training_text
    except Exception as e:
        logger.error(f"Erro ao carregar contexto de treinamento: {e}")
        return ""

TRAINING_CONTEXT = load_training_context()
FULL_SYSTEM_PROMPT = SYSTEM_PROMPT + TRAINING_CONTEXT

def safe_decode_unicode(s: str) -> str:
    try:
        import re
        import codecs
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

        self.providers = [
            {"name": "litert", "client": self.litert_client, "model": "gemma3-1b-it", "timeout": 3.0},
            {"name": "ollama", "client": self.ollama_client, "model": os.getenv("OLLAMA_MODEL", "gemma:2b"), "timeout": 10.0},
            {"name": "mistral", "client": self.mistral_client, "model": mistral_model, "timeout": 15.0},
            {"name": "groq", "client": self.groq_client, "model": "llama-3.3-70b-versatile", "timeout": 10.0},
            {"name": "openrouter", "client": self.openrouter_client, "model": "openrouter/free", "timeout": 20.0},
        ]

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        """Alias de compatibilidade com PASAAuditor e AdProcessor."""
        return await self.classify_text(text, comment_id)

    async def classify_text(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        self.providers.sort(key=lambda p: ai_circuit_breaker.failures.get(p["name"], 0))
        local_result = None
        
        # CAMADA 1: FILTRAGEM LOCAL
        for provider in self.providers:
            if provider["name"] not in ["litert", "ollama"] or not ai_circuit_breaker.can_execute(provider["name"]):
                continue
            try:
                res = await self._call_provider(provider, text, comment_id)
                if res:
                    local_result = res
                    # Só encerra se for lixo ou neutro com alta confiança (sem contradição interna)
                    if not res.get("low_confidence") and (res.get("categoria_ia") == "LIXO" or res.get("categoria_ia") == "NEUTRO"):
                        logger.info(f"🟢 [AI] {provider['name'].upper():<10} | ID: {comment_id:<36} | {res['categoria_ia']:<20} | {res['confianca_ia']:.2f} | (Filtragem Local)")
                        return res
                    break
            except: continue

        # CAMADA 2: PERÍCIA CLOUD (Refinamento)
        for provider in self.providers:
            if provider["name"] in ["litert", "ollama"] or not ai_circuit_breaker.can_execute(provider["name"]):
                continue
            try:
                hint = f" [Sugestão Local: {local_result.get('categoria_ia')}]" if local_result else ""
                res = await self._call_provider(provider, text + hint, comment_id)
                if res:
                    source = local_result["name"] if local_result else "NONE"
                    logger.info(f"🔍 [AI] {provider['name'].upper():<10} | ID: {comment_id:<36} | {res['categoria_ia']:<20} | {res['confianca_ia']:.2f} | (Refinado de {source})")
                    return res
            except: continue

        if local_result:
            logger.warning(f"⚠️ [AI] Cloud falhou. Usando local fallback para {comment_id}.")
            return local_result
        raise RuntimeError(f"Todas as camadas falharam para {comment_id}.")

    async def _call_provider(self, provider: Dict[str, Any], text: str, comment_id: str) -> Optional[Dict[str, Any]]:
        name = provider["name"]
        system_prompt = LOCAL_SYSTEM_PROMPT if name in ["litert", "ollama"] else FULL_SYSTEM_PROMPT
        try:
            response = await provider["client"].chat.completions.create(
                model=provider["model"],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Comentário: \"{text}\""}],
                response_format={"type": "json_object"},
                temperature=0.0,
                timeout=provider.get("timeout", 15.0)
            )
            result = self._parse_json_response(response.choices[0].message.content)
            result["name"] = name
            ai_circuit_breaker.record_success(name)
            return result
        except Exception as e:
            ai_circuit_breaker.record_failure(name, getattr(e, "status_code", None))
            return None

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content.replace("```json", "").replace("```", "").strip())
            conf_val = data.get("confianca_ia", data.get("confidence"))
            confidence = float(conf_val) if conf_val is not None else 0.70
            categoria = data.get("categoria_ia", data.get("category", "NEUTRO"))
            analise = data.get("analise_pericial", "").lower()
            
            # --- DETECÇÃO DE CONTRADIÇÃO (Escalação Automática) ---
            attack_keywords = ["ataque", "hostil", "ofensiv", "insulto", "ódio", "ironia", "velad", "crítica pessoal"]
            if categoria == "NEUTRO" and any(k in analise for k in attack_keywords):
                confidence = 0.40 # Força escalação
                
            low_conf = confidence < CONFIDENCE_THRESHOLD
            return {
                "is_hate": bool(data.get("is_hate", False)),
                "categoria_ia": categoria,
                "category": categoria, # Alias compatibilidade
                "confianca_ia": confidence,
                "confidence": confidence, # Alias compatibilidade
                "evidencia_lexical": data.get("evidencia_lexical", []),
                "analise_pericial": data.get("analise_pericial", "Sem análise"),
                "low_confidence": low_conf
            }
        except:
            return {"is_hate": False, "categoria_ia": "NEUTRO", "category": "NEUTRO", "confianca_ia": 0.0, "confidence": 0.0, "analise_pericial": "Erro parsing"}

    async def validate_identity(self, expected_name: str, display_name: str, bio: str, followers: str = "0", is_verified: bool = False) -> Dict[str, Any]:
        prompt = (f"Valide identidade de figura pública: {expected_name}\nPerfil: {display_name} | Bio: {bio} | Seguidores: {followers}\n"
                 f"Seja tolerante se for verificado ou popular. Marque inautêntico apenas se for paródia/fã-clube.")
        try:
            response = await self.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except: return {"is_authentic": True, "reason": "erro_ia"}

    async def run_batch_classification(self, limit: int = 50) -> int:
        from core.supabase_service import supabase as db
        try:
            res = db.table("comentarios").select("id, texto_bruto, cluster_id").eq("processado_ia", False).limit(limit).execute()
            comments = res.data or []
            if not comments: return 0
            
            count = 0
            cluster_results = {} # Cache de resultados por cluster_id

            for c in comments:
                cluster_id = c.get("cluster_id")
                
                # Se o comentário faz parte de um cluster já processado neste lote
                if cluster_id and cluster_id in cluster_results:
                    res_ia = cluster_results[cluster_id]
                    logger.info(f"🔁 [AI] Replicando resultado de Cluster Coordenado para {c['id']}")
                else:
                    try:
                        res_ia = await self.classify_text(c["texto_bruto"], comment_id=str(c["id"]))
                        if cluster_id:
                            cluster_results[cluster_id] = res_ia # Armazena para os próximos
                    except:
                        continue

                try:
                    db.table("comentarios").update({
                        "processado_ia": True,
                        "is_hate": res_ia["is_hate"],
                        "categoria_ia": "CAMPANHA_COORDENADA" if cluster_id else res_ia["categoria_ia"],
                        "confianca_ia": res_ia["confianca_ia"],
                        "analise_pericial": f"[COORDINATED] {res_ia['analise_pericial']}" if cluster_id else res_ia["analise_pericial"],
                    }).eq("id", c["id"]).execute()
                    count += 1
                except: continue
            return count
        except: return 0

ai_service = AIService()
