# -*- coding: utf-8 -*-
"""
core/scrapfly_service.py - Cliente de Integração Scrapfly (PASA v98.9)
════════════════════════════════════════════════════════════════════
Fornece conectividade robusta à API do Scrapfly para Web Scraping na nuvem
com desvio de anti-bot (ASP) e renderização JS remota.
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any

logger = logging.getLogger("core.scrapfly_service")

class ScrapflyService:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.getenv("SCRAPFLY_API_KEY")
        self.api_url = "https://api.scrapfly.io/scrape"
        
        if not self.api_key:
            logger.warning("⚠️ SCRAPFLY_API_KEY não configurada no arquivo .env. Scrapfly indisponível.")

    async def scrape(
        self,
        url: str,
        render_js: bool = True,
        asp: bool = True,
        tags: str = "project:default,player",
        timeout: float = 60.0
    ) -> Optional[Dict[str, Any]]:
        """
        Executa requisição de raspagem na nuvem via Scrapfly.
        """
        if not self.api_key:
            logger.error("❌ Scrapfly API Key ausente.")
            return None

        params = {
            "key": self.api_key,
            "url": url,
            "render_js": "true" if render_js else "false",
            "asp": "true" if asp else "false",
            "tags": tags
        }

        try:
            logger.info(f"🌐 [Scrapfly] Iniciando raspagem: {url}...")
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(self.api_url, params=params)
                
                if resp.status_code == 402:
                    logger.error("❌ [Scrapfly] Falha por falta de créditos (402 Payment Required).")
                    return {"success": False, "error": "insufficient_credits"}
                elif resp.status_code != 200:
                    logger.error(f"❌ [Scrapfly] API retornou HTTP {resp.status_code}: {resp.text}")
                    return {"success": False, "error": f"http_error_{resp.status_code}"}

                data = resp.json()
                if "result" in data:
                    result = data["result"]
                    logger.info(f"✅ [Scrapfly] Sucesso! Status da página: {result.get('status_code')}, tamanho: {len(result.get('content', ''))} caracteres.")
                    return {
                        "success": True,
                        "status_code": result.get("status_code"),
                        "content": result.get("content"),
                        "content_type": result.get("content_type"),
                        "url": result.get("url"),
                        "duration": result.get("duration")
                    }
                else:
                    logger.error("❌ [Scrapfly] Formato de resposta inválido (campo 'result' ausente).")
                    return {"success": False, "error": "invalid_response_format"}

        except Exception as e:
            logger.error(f"❌ [Scrapfly] Falha inesperada durante requisição: {e}")
            return {"success": False, "error": str(e)}

# Instância única global do serviço
scrapfly_service = ScrapflyService()
