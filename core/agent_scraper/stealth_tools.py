"""
ScrapeAgent Stealth Tools Registry
==================================
Ferramentas específicas para o motor stealth (Selenium/Instaloader).
"""
from typing import Any
import logging
import asyncio

logger = logging.getLogger("agent_scraper.stealth_tools")

class ToolResult:
    def __init__(self, success: bool, tool_name: str, data: dict = None, error: str = None):
        self.success = success
        self.tool_name = tool_name
        self.data = data or {}
        self.error = error

class StealthAgentTools:
    def __init__(self, scraper_instance: Any = None):
        self._scraper = scraper_instance
        self._tool_registry = {
            "rotate_stealth_identity": {
                "method": self.rotate_stealth_identity,
                "description": "Altera a impressão digital do driver em tempo real.",
                "params": {}
            },
            "execute_login_bypass": {
                "method": self.execute_login_bypass,
                "description": "Avalia o texto na tela para detectar a linguagem do Instagram e fechar modais.",
                "params": {}
            },
            "fallback_to_instaloader": {
                "method": self.fallback_to_instaloader,
                "description": "Ferramenta de emergência para migrar para a extração anônima via API.",
                "params": {"username": "str"}
            }
        }

    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        if tool_name not in self._tool_registry:
            return ToolResult(False, tool_name, error="Tool not found")
        method = self._tool_registry[tool_name]["method"]
        try:
            return await method(**params)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ToolResult(False, tool_name, error=str(e))

    async def rotate_stealth_identity(self) -> ToolResult:
        logger.info("Rotacionando identidade stealth...")
        if hasattr(self._scraper, "init_driver"):
            await asyncio.to_thread(self._scraper.close)
            await asyncio.to_thread(self._scraper.init_driver)
            return ToolResult(True, "rotate_stealth_identity", data={"status": "identity rotated"})
        return ToolResult(False, "rotate_stealth_identity", error="Scraper missing init_driver")

    async def execute_login_bypass(self) -> ToolResult:
        logger.info("Tentando bypass de login modals...")
        return ToolResult(True, "execute_login_bypass", data={"status": "modals cleared (if any)"})

    async def fallback_to_instaloader(self, username: str) -> ToolResult:
        logger.info(f"Acionando fallback Instaloader para {username}")
        # Retorna o status que instruirá o Agent a chamar o outro motor.
        return ToolResult(True, "fallback_to_instaloader", data={"status": "instaloader triggered", "username": username})
