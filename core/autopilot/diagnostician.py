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
        prompt = (
            f"Analise os logs de erro do sistema Sentinela abaixo e identifique a causa raiz.\n"
            f"Logs:\n{logs}\n\n"
            f"Responda APENAS com JSON:\n"
            f"{{\"type\": \"DOM_CHANGE|IP_BLOCK|SESSION_EXPIRED|CODE_BUG\", \"reason\": \"descrição\", \"confidence\": float}}"
        )
        try:
            # Usa o AIService para análise semântica
            # Nota: No v70.0 real, usaríamos um modelo mais robusto como o Gemini 1.5 Pro
            res = await self.ai.classify_text(prompt)
            return res
        except Exception as e:
            logger.error(f"Erro no diagnóstico de log: {e}")
            return {"type": "UNKNOWN", "reason": str(e), "confidence": 0.0}

    async def analyze_page_html(self, html: str, target_selector: str) -> Dict[str, Any]:
        """Analisa o HTML de uma página para sugerir novos seletores."""
        # Truncate HTML to avoid token limits
        truncated_html = html[:15000]
        prompt = (
            f"O seletor '{target_selector}' falhou na extração.\n"
            f"HTML da página:\n{truncated_html}\n\n"
            f"Encontre o novo seletor CSS/XPath para os comentários.\n"
            f"Responda APENAS com JSON:\n"
            f"{{\"new_selector\": \"string\", \"explanation\": \"string\"}}"
        )
        try:
            res = await self.ai.classify_text(prompt)
            return res
        except Exception as e:
            logger.error(f"Erro no diagnóstico de HTML: {e}")
            return {"new_selector": None, "explanation": str(e)}

diagnostician = Diagnostician()
