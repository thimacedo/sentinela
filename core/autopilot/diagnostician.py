"""
Diagnostician v51.0 — PASA
═══════════════════════════
Diagnóstico de falhas sem LLM para casos comuns (sessão, rede, rate limit, DOM).
LLM é reservado APENAS para DOM_CHANGE, onde análise semântica tem valor real.
"""
import logging
import re
from typing import Dict, Any

logger = logging.getLogger("core.autopilot.diagnostician")

# Regras determinísticas — zero tokens de LLM para erros de infra
_REGRAS: Dict[str, list] = {
    "SESSION_EXPIRED": ["session", "login", "cookie", "expired", "auth", "sessao", "sessão", "credencial"],
    "RATE_LIMIT":      ["429", "rate limit", "too many", "blocked", "bloqueado", "throttl"],
    "NETWORK":         ["timeout", "connection", "refused", "unreachable", "conexão", "conection error", "net::err"],
    "IP_BLOCK":        ["ip block", "challenge", "captcha", "checkpoint", "banned"],
    "CODE_BUG":        ["attributeerror", "typeerror", "indexerror", "keyerror", "nameerror", "exception"],
}

_SUGESTOES: Dict[str, str] = {
    "SESSION_EXPIRED": "Sessão expirada. Verificar e renovar cookies do Instagram.",
    "RATE_LIMIT":      "Rate limit atingido. Aumentar jitter e reduzir frequência de coleta.",
    "NETWORK":         "Falha de rede transitória. Aguardar recuperação automática.",
    "IP_BLOCK":        "IP bloqueado. Verificar configuração de proxy ou aguardar cooldown.",
    "CODE_BUG":        "Erro de código detectado. Revisar logs detalhados e corrigir.",
    "UNKNOWN":         "Erro desconhecido. Verificar logs detalhados.",
}


def _classify_error(error_text: str) -> str:
    """Classifica o tipo de erro por regex sem LLM."""
    error_lower = (error_text or "").lower()
    for tipo, palavras in _REGRAS.items():
        if any(p in error_lower for p in palavras):
            return tipo
    return "UNKNOWN"


class Diagnostician:
    """
    Analista de falhas v51.0 — regras determinísticas + LLM apenas para DOM_CHANGE.
    """

    def __init__(self, ai_service=None):
        from core.ai_service import ai_service as default_ai
        self.ai = ai_service or default_ai

    async def analyze_log_segment(self, logs: str) -> Dict[str, Any]:
        """Analisa log de erro. Usa regex para erros comuns; LLM apenas para DOM_CHANGE."""
        tipo = _classify_error(logs)

        # LLM apenas quando não há regra clara e pode ser mudança de DOM (estrutural)
        if tipo == "UNKNOWN" and len(logs) > 50:
            try:
                system_prompt = "Você é um engenheiro de SRE especializado em coletores de dados do Instagram."
                prompt = (
                    f"Analise os logs de erro abaixo e identifique a causa raiz técnica.\n"
                    f"Logs:\n{logs[:3000]}\n\n"
                    f"Responda APENAS com JSON:\n"
                    f"{{\"type\": \"DOM_CHANGE|IP_BLOCK|SESSION_EXPIRED|CODE_BUG|UNKNOWN\","
                    f" \"reason\": \"descrição curta\", \"confidence\": float}}"
                )
                res = await self.ai.chat_completion(prompt, system_prompt=system_prompt)
                if res and isinstance(res, dict):
                    return res
            except Exception as e:
                logger.warning("[Diagnostician] Falha no fallback LLM: %s", e)

        return {
            "type": tipo,
            "reason": _SUGESTOES.get(tipo, "Erro desconhecido."),
            "confidence": 0.9 if tipo != "UNKNOWN" else 0.4
        }

    async def analyze_page_html(self, html: str, target_selector: str) -> Dict[str, Any]:
        """Analisa HTML para sugerir novo seletor CSS — LLM justificado aqui."""
        truncated_html = html[:12000]
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
            return {"new_selector": None, "explanation": "IA não retornou resposta."}
        except Exception as e:
            logger.error("[Diagnostician] Erro no diagnóstico de HTML: %s", e)
            return {"new_selector": None, "explanation": str(e)}


diagnostician = Diagnostician()
