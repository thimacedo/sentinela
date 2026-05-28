import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger("core.autopilot.diagnostician")

class Diagnostician:
    """
    Analista de IA para diagnóstico de falhas (PASA v70.0).
    Identifica padrões de erro em logs e HTML.
    """
    def __init__(self, ai_service=None):
        from core.ai_service import ai_service as default_ai
        self.ai = ai_service or default_ai

    async def analyze_log_segment(self, logs: str) -> Dict[str, Any]:
        """Analisa um segmento de log para identificar a causa raiz."""
        system_prompt = "Você é um engenheiro de SRE especializado em depuração de coletores de dados do Instagram."
        prompt = (
            f"Analise os logs de erro do sistema Sentinela abaixo e identifique a causa raiz técnica.\n"
            f"Logs:\n{logs}\n\n"
            f"Responda APENAS com JSON:\n"
            f"{{\"type\": \"DOM_CHANGE|IP_BLOCK|SESSION_EXPIRED|CODE_BUG|UNKNOWN\", \"reason\": \"descrição curta\", \"confidence\": float}}"
        )
        try:
            # Usa o AIService para análise técnica genérica
            res = await self.ai.chat_completion(prompt, system_prompt=system_prompt)
            if res:
                return res
            return {"type": "UNKNOWN", "reason": "IA não retornou resposta", "confidence": 0.0}
        except Exception as e:
            logger.error(f"Erro no diagnóstico de log: {e}")
            return {"type": "UNKNOWN", "reason": str(e), "confidence": 0.0}

    async def analyze_page_html(self, html: str, target_selector: str) -> Dict[str, Any]:
        """Analisa o HTML de uma página para sugerir novos seletores."""
        truncated_html = html[:15000]
        system_prompt = "Você é um especialista em extração de dados (Web Scraping)."
        prompt = (
            f"O seletor '{target_selector}' falhou.\n"
            f"HTML da página:\n{truncated_html}\n\n"
            f"Sugira um novo seletor CSS robusto para extrair os comentários.\n"
            f"Responda APENAS com JSON:\n"
            f"{{\"new_selector\": \"string\", \"explanation\": \"string\"}}"
        )
        try:
            res = await self.ai.chat_completion(prompt, system_prompt=system_prompt)
            if res:
                return res
            return {"new_selector": None, "explanation": "IA não retornou resposta"}
        except Exception as e:
            logger.error(f"Erro no diagnóstico de HTML: {e}")
            return {"new_selector": None, "explanation": str(e)}

diagnostician = Diagnostician()
