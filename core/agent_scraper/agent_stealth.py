"""
ScrapeAgent Stealth Cognitive Loop
==================================
Implementa o ciclo OODA para o motor legado Stealth Scraper.
"""
import logging
from typing import Any, Dict
from core.agent_scraper.stealth_tools import StealthAgentTools

logger = logging.getLogger("agent_scraper.stealth")

class StealthAgentOODA:
    def __init__(self, scraper_instance: Any, ai_service: Any = None):
        self.scraper = scraper_instance
        self.ai = ai_service
        self.tools = StealthAgentTools(scraper_instance)
        self.state = "INIT"

    async def observe(self, context: Dict) -> Dict:
        """Coleta o estado atual (ex: URL atual, presença de popup, bloqueios)."""
        logger.info("Observing current DOM state...")
        
        current_url = context.get("current_url", "https://www.instagram.com/")
        status_code = context.get("status_code", 200)
        
        # Detecta bloqueio baseado em status HTTP ou keywords na URL
        blocked = False
        if status_code in (403, 429):
            blocked = True
        elif any(keyword in current_url.lower() for keyword in ["login", "challenge", "checkpoint", "scraping_warning"]):
            blocked = True
            
        return {
            "current_url": current_url, 
            "has_modal": context.get("has_modal", False), 
            "blocked": blocked,
            "context": context
        }

    async def orient(self, observation: Dict) -> str:
        """Determina a próxima ação com base na observação."""
        logger.info("Orienting based on observation...")
        if observation.get("has_modal"):
            return "execute_login_bypass"
        if observation.get("blocked", False):
            return "rotate_stealth_identity"
        return "continue"

    async def decide(self, action_intent: str) -> str:
        """Valida a intenção e define a ferramenta final."""
        if action_intent in ["execute_login_bypass", "rotate_stealth_identity", "fallback_to_instaloader"]:
            return action_intent
        return "none"

    async def act(self, tool_name: str, context: Dict) -> Dict:
        """Aciona a ferramenta e retorna o resultado."""
        if tool_name == "none":
            return {"status": "success", "message": "No action needed"}
        
        logger.info(f"Acting: executing {tool_name}")
        result = await self.tools.execute(tool_name, {})
        return {"status": "success" if result.success else "error", "tool": tool_name, "data": result.data}

    async def run_cycle(self, context: Dict) -> Dict:
        """Executa um ciclo OODA completo."""
        obs = await self.observe(context)
        intent = await self.orient(obs)
        decision = await self.decide(intent)
        result = await self.act(decision, context)
        return result
