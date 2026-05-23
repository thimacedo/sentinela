"""
PASA v49 - AI Service: Motor de Inteligência Resiliente (Cloud Only)
Cascata de IAs (Groq -> Mistral -> OpenRouter) com Circuit Breaker.
Sem dependências locais de LLM para preservar a memória do servidor.
"""
import os
import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

logger = logging.getLogger("SentinelaAI")

# Prompt baseado no PADRONIZACAO_LINGUISTICA_FORENSE.md (MCA v2.2)
SYSTEM_PROMPT = """Você é um analista forense digital do sistema Sentinela Democrática.
Analise o comentário político abaixo e classifique seguindo o protocolo PASA.
Responda APENAS com JSON válido contendo:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO" | "XENOFOBIA_REGIONAL" | "RACISMO_RELIGIOSO" | "VIOLÊNCIA_GÊNERO" | "MILICIA_DIGITAL" | "RACISMO_ESTRUTURAL" | "MISOGINIA_POLITICA",
  "confianca_ia": float (0.0 a 1.0),
  "evidencia_lexical": ["termo1", "termo2"],
  "analise_pericial": "Breve justificativa em pt-BR"
}"""

class AIService:
    def __init__(self):
        # 1. Groq (Mais rápido, limite de RPM menor)
        self.groq_client = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        # 2. Mistral (Preciso em PT-BR, tier gratuito sustentável)
        self.mistral_client = AsyncOpenAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            base_url="https://api.mistral.ai/v1"
        )
        
        # 3. OpenRouter (Rede de segurança gratuita, fallback final)
        self.openrouter_client = AsyncOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

        # Ordem de prioridade para classificação (Cloud Only)
        self.providers = [
            {"name": "groq", "client": self.groq_client, "model": "llama3-8b-8192"},
            {"name": "mistral", "client": self.mistral_client, "model": "open-mistral-nemo"},
            {"name": "openrouter", "client": self.openrouter_client, "model": "meta-llama/llama-3.1-8b-instruct:free"},
        ]

    async def classify_text(self, text: str) -> Dict[str, Any]:
        """Tenta classificar o texto em cascata, respeitando o Circuit Breaker."""
        
        for provider in self.providers:
            name = provider["name"]
            
            # 🛡️ Verifica se o circuito está aberto antes de tentar
            if not ai_circuit_breaker.can_execute(name):
                continue

            try:
                response = await provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Comentário: \"{text}\""}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    timeout=15.0
                )
                
                content = response.choices[0].message.content
                result = self._parse_json_response(content)
                
                ai_circuit_breaker.record_success(name)
                logger.info(f"📊 [AI] {name.upper()} | {result.get('categoria_ia', 'ERRO')} | {result.get('confianca_ia', 0):.2f}")
                return result

            except APIStatusError as e:
                ai_circuit_breaker.record_failure(name, e.status_code)
                logger.warning(f"⚠️ [AI] {name.upper()} falhou (HTTP {e.status_code}). Acionando Fallback...")
            except Exception as e:
                ai_circuit_breaker.record_failure(name, None)
                logger.warning(f"⚠️ [AI] {name.upper()} falhou ({type(e).__name__}). Acionando Fallback...")

        # Se chegou aqui, TODAS as IAs cloud falharam ou estão com circuito aberto
        raise RuntimeError("Todas as APIs de IA cloud estão indisponíveis ou com circuito aberto.")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Extrai e valida o JSON retornado pela IA."""
        try:
            data = json.loads(content)
            return {
                "is_hate": bool(data.get("is_hate", False)),
                "categoria_ia": data.get("categoria_ia", "NEUTRO"),
                "confianca_ia": float(data.get("confianca_ia", 0.0)),
                "evidencia_lexical": data.get("evidencia_lexical", []),
                "analise_pericial": data.get("analise_pericial", "Sem análise")
            }
        except json.JSONDecodeError:
            logger.error(f"❌ [AI] Resposta não é JSON válido: {content[:100]}")
            return {
                "is_hate": False,
                "categoria_ia": "NEUTRO",
                "confianca_ia": 0.0,
                "evidencia_lexical": [],
                "analise_pericial": "Erro de parsing JSON"
            }

    async def run_batch_classification(self, limit: int = 50) -> int:
        """Busca comentários não processados e classifica em lote."""
        from core.supabase_service import supabase as db
        
        try:
            # 1. Busca comentários pendentes
            res = db.table("comentarios").select("id, texto_bruto").eq("processado_ia", False).limit(limit).execute()
            comments = res.data if res.data else []
            
            if not comments:
                return 0
                
            processed_count = 0
            for comment in comments:
                try:
                    # 2. Classifica cada um
                    result = await self.classify_text(comment["texto_bruto"])
                    
                    # 3. Persiste o resultado
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
                    logger.error(f"❌ Erro ao processar comentário {comment['id']}: {e}")
                    
            return processed_count
        except Exception as e:
            logger.error(f"💥 Falha crítica no lote de classificação: {e}")
            return 0

# Instância Singleton
ai_service = AIService()
