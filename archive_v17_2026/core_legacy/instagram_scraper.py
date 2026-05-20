# instagram_scraper.py - Integração Final Stealth + Behavior
import asyncio
import logging
from playwright.async_api import async_playwright
from core.stealth_playwright import StealthBrowser
from core.session_manager import SessionManager
from core.behavior_engine import BehaviorEngine

class IntegratedInstagramScraper:
    """Scraper de elite integrado com Camada Stealth e PASA v16.4"""
    def __init__(self, target_profile: str):
        self.target_profile = target_profile
        self.logger = logging.getLogger("Sentinela.IntegratedScraper")
        self.session_mgr = SessionManager()
        self.stealth = StealthBrowser(headless=True)

    async def run(self):
        async with async_playwright() as p:
            proxy = self.session_mgr.get_proxy_config()
            context = await self.stealth.get_stealth_context(p, proxy=proxy)
            
            cookies = self.session_mgr.load_session(self.target_profile)
            if cookies:
                await context.add_cookies(cookies)
                
            page = await context.new_page()
            behavior = BehaviorEngine(page)
            
            try:
                url = f"https://www.instagram.com/{self.target_profile}/"
                self.logger.info(f"Navegando para {url}...")
                await page.goto(url, wait_until="networkidle")
                
                await behavior.simulate_idle()
                await behavior.random_scroll()
                
                content = await page.title()
                self.logger.info(f"Conteúdo capturado: {content}")
                
                updated_cookies = await context.cookies()
                self.session_mgr.save_session(self.target_profile, updated_cookies)
                
                return {"status": "success", "data": content}
            except Exception as e:
                self.logger.error(f"Erro na extração: {e}")
                return {"status": "error", "message": str(e)}
            finally:
                await context.close()
