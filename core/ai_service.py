"""
PASA v52.3 - AI Service: Motor de Inteligência Resiliente (Hybrid Cascade)
Roteamento dinâmico: LiteRT (Local) -> Ollama (Local) -> Mistral -> Groq -> OpenRouter.
"""
import os
import json
import logging
logger = logging.getLogger("AIService")
from typing import Dict, Any, List
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))

# MCA v2.2 Protocol
SYSTEM_PROMPT = """Você é um analista forense digital do sistema Sentinela Democrática, especializado em política brasileira.
Sua missão é classificar comentários políticos com precisão cirúrgica, detectando ódio e hostilidade mesmo quando disfarçados de ironia.

--- REGRAS DE CLASSIFICAÇÃO (ESTRITAS) ---

1. CLASSIFIQUE COMO "LIXO" APENAS SE FOR:
   - Elementos de interface técnica (ex: "Ver tradução", "Instagram Lite", "Responder", "1 sem").
   - Apenas marcações de perfis sem texto adicional (ex: "@fulano").
   - Sequências puras de emojis sem qualquer texto (ex: "😂😂😂😂").
   - Localizações geográficas isoladas (ex: "Brasília - DF").
   
2. NUNCA CLASSIFIQUE COMO "LIXO":
   - Referências a memes políticos ou jargões (ex: "TOC TOC TOC", "Faz o L", "O amor venceu", "Visconde de Sabugosa").
   - Perguntas retóricas sobre crimes ou políticos (ex: "E a condenação?", "Cade o pix?").
   - Gírias brasileiras ou abreviações (ex: "vcs", "tá torando", "tá com o 👌🏻 na mão").
   - Críticas ácidas, mesmo que curtas.

--- DIRETRIZES DE SARCASMO E ÓDIO (MCA v2.2) ---
A ironia é usada para mascarar o ódio. Marque "is_hate": true e use a categoria adequada para:
- MISOGINIA_POLITICA: Ataques a mulheres focados em aparência, histeria, "meninas de fulano", ou "lugar de mulher". OBSERVAÇÃO: Esta categoria é EXCLUSIVA para alvos do sexo feminino. Se termos femininos forem usados para insultar um homem (ex: chamar um político homem de "histérica" ou "menina"), classifique obrigatoriamente como INSULTO_AD_HOMINEM.
- MILICIA_DIGITAL: Ataques coordenados a instituições, descrédito do sistema eleitoral, ad hominem pesado, acusações de corrupção sem provas ("Ladrão", "Corrupto") ou memes de perseguição política ("TOC TOC TOC").
- RACISMO_ESTRUTURAL: Deboche de pautas raciais ou uso de termos como "escravo", "capitão do mato" em tom político.

Responda APENAS com JSON válido:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO" | "XENOFOBIA_REGIONAL" | "RACISMO_RELIGIOSO" | "VIOLÊNCIA_GÊNERO" | "MILICIA_DIGITAL" | "RACISMO_ESTRUTURAL" | "MISOGINIA_POLITICA" | "ATAQUE_INSTITUCIONAL" | "INSULTO_AD_HOMINEM" | "LIXO",
  "confianca_ia": float (0.0 a 1.0),
  "evidencia_lexical": ["termo1", "termo2"],
  "analise_pericial": "Breve justificativa técnica em pt-BR"
}

--- EXEMPLOS DE CALIBRAÇÃO ---
- "Visconde de Sabugosa virando sabugo." -> { "is_hate": true, "categoria_ia": "INSULTO_AD_HOMINEM", "analise_pericial": "Ataque pessoal (ad hominem) usando apelido depreciativo." }
- "TOC TOC TOC" -> { "is_hate": false, "categoria_ia": "NEUTRO", "analise_pericial": "Meme político sobre operações policiais (PF). Neutro sem ameaça." }
- "Filho bandid0? Que isso??" -> { "is_hate": false, "categoria_ia": "NEUTRO", "analise_pericial": "Questionamento sobre figuras públicas e legalidade." }
- "Tá com o 👌🏻 torando!!!" -> { "is_hate": false, "categoria_ia": "NEUTRO", "analise_pericial": "Gíria brasileira para tensão extrema. Não é lixo." }
- "PRIVATIZA A USP JÁ" -> { "is_hate": true, "categoria_ia": "ATAQUE_INSTITUCIONAL", "analise_pericial": "Ataque ou demanda hostil contra instituição pública de ensino." }
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
                # Extrai apenas o trecho do texto do prompt do dataset
                prompt_text = data.get("prompt", "")
                if "Texto:" in prompt_text:
                    excerpt = prompt_text.split("Texto:")[1].strip()
                    training_text += f"- {excerpt}\n"
                    # Limite de segurança de tokens para evitar travamento em modelos locais menores
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
        # 00. LiteRT (Local High-Speed - Gemma 3 1B)
        self.litert_client = AsyncOpenAI(
            api_key="litert",
            base_url=os.getenv("LITERT_BASE_URL", "http://localhost:9379/v1")
        )

        # 0. Ollama (Local - Gemma 2B)
        self.ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        )

        # 1. Mistral (Cloud Primary)
        self.mistral_client = AsyncOpenAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            base_url="https://api.mistral.ai/v1"
        )

        # 2. Groq (Cloud Fast)
        self.groq_client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        # 3. OpenRouter (Cloud Safety)
        self.openrouter_client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

        # Configurações de Modelos
        finetuned_model = os.getenv('FINETUNED_MODEL_NAME')
        mistral_model = finetuned_model if finetuned_model else "open-mistral-nemo"

        self.providers = []
        
        # Priorização de Camadas (Tiers)
        
        # Tier 00: LiteRT (Iniciativa Local de Altíssima Velocidade)
        self.providers.append({
            "name": "litert", 
            "client": self.litert_client, 
            "model": "gemma3-1b-gpu-custom",
            "timeout": 5.0
        })

        # Tier 0: Ollama
        if os.getenv("ENABLE_LOCAL_AI", "false").lower() == "true":
            self.providers.append({
                "name": "ollama", 
                "client": self.ollama_client, 
                "model": os.getenv("OLLAMA_MODEL", "gemma:2b"),
                "timeout": 15.0
            })

        # Camadas Cloud
        self.providers.extend([
            {"name": "mistral", "client": self.mistral_client, "model": mistral_model, "timeout": 15.0},
            {"name": "groq", "client": self.groq_client, "model": "llama-3.3-70b-versatile", "timeout": 10.0},
            {"name": "openrouter", "client": self.openrouter_client, "model": "openrouter/free", "timeout": 20.0},
        ])

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        """Alias para classify_text para compatibilidade com PASAAuditor."""
        return await self.classify_text(text, comment_id)

    async def classify_text(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        """Tenta classificar o texto em cascata, reordenando dinamicamente por saúde."""
        
        # 1. Reordenar provedores: Provedores com falhas recentes vão para o fim da fila
        self.providers.sort(key=lambda p: ai_circuit_breaker.failures.get(p["name"], 0))

        for provider in self.providers:
            name = provider["name"]
            
            # 🛡️ Verifica se o circuito está aberto para o provedor
            if not ai_circuit_breaker.can_execute(name):
                logger.info(f"⏭️  [AI] {name.upper():<10} | ID: {comment_id:<36} | STATUS: INDISPONÍVEL")
                continue

            try:
                response = await provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[
                        {"role": "system", "content": FULL_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Comentário: \"{text}\""}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    timeout=provider.get("timeout", 15.0)
                )
                
                content = response.choices[0].message.content
                result = self._parse_json_response(content)
                result = clean_null_chars(result)
                
                ai_circuit_breaker.record_success(name)
                
                decoded_text = safe_decode_unicode(text)
                clean_text = decoded_text.replace("\n", " ").replace("\r", " ").strip()
                # Truncate to ensure log line doesn't explode in size
                truncated_text = clean_text if len(clean_text) <= 50 else clean_text[:47] + "..."
                
                # Log padronizado com larguras fixas:
                # [AI] 10 chars | ID: 36 chars | CATEGORIA: 20 chars | CONF: 4 chars | TEXTO
                cat = result.get('categoria_ia', 'NEUTRO')
                conf = result.get('confianca_ia', 0.0)
                logger.info(f"📊  [AI] {name.upper():<10} | ID: {comment_id:<36} | {cat:<20} | {conf:.2f} | \"{truncated_text}\"")
                return result

            except Exception as e:
                status_code = getattr(e, "status_code", None)
                ai_circuit_breaker.record_failure(name, status_code)
                
                logger.warning(f"⚠️  [AI] {name.upper():<10} | ID: {comment_id:<36} | STATUS: FALHA/TIMEOUT | ERRO: {str(e)[:50]}")

        raise RuntimeError(f"Todas as camadas de IA falharam para o comentário {comment_id}.")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content)
            confidence = float(data.get("confianca_ia", 0.0))
            low_conf = confidence < CONFIDENCE_THRESHOLD
            categoria = data.get("categoria_ia", "NEUTRO")
            
            if categoria == "LIXO":
                confidence = 0.0
                low_conf = False
                is_hate = False
            else:
                if low_conf: categoria = "INDEFINIDO"
                is_hate = bool(data.get("is_hate", False))
            
            return {
                "is_hate": is_hate,
                "categoria_ia": categoria,
                "confianca_ia": confidence,
                "evidencia_lexical": data.get("evidencia_lexical", []),
                "analise_pericial": data.get("analise_pericial", "Sem análise"),
                "low_confidence": low_conf
            }
        except:
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 0.0, "evidencia_lexical": [], "analise_pericial": "Erro de parsing"}

    async def run_batch_classification(self, limit: int = 50) -> int:
        from core.supabase_service import supabase as db
        try:
            res = db.table("comentarios").select("id, texto_bruto").eq("processado_ia", False).limit(limit).execute()
            comments = res.data or []
            if not comments: return 0
                
            processed_count = 0
            for comment in comments:
                try:
                    # Passando o ID real do comentário para o log
                    result = await self.classify_text(comment["texto_bruto"], comment_id=str(comment["id"]))
                    db.table("comentarios").update({
                        "processado_ia": True,
                        "is_hate": result["is_hate"],
                        "categoria_ia": result["categoria_ia"],
                        "confianca_ia": result["confianca_ia"],
                        "evidencia_lexical": result["evidencia_lexical"],
                        "analise_pericial": result["analise_pericial"],
                    }).eq("id", comment["id"]).execute()
                    processed_count += 1
                except Exception as e:
                    logger.error(f"❌ Erro ao classificar comentário {comment.get('id')}: {str(e)}")
                    continue
            return processed_count
        except Exception as e:
            logger.error(f"💥 Falha crítica no lote de classificação de IA: {str(e)}")
            return 0

ai_service = AIService()
