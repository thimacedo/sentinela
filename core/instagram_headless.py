import time
import os
import re
import json
import random
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from processing.text_processor import clean_comment

logger = logging.getLogger("instagram_headless")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
IG_USER = os.getenv("IG_USER")
IG_PASS = os.getenv("IG_PASS")
INSTAGRAM_SESSIONID = os.getenv("INSTAGRAM_SESSIONID")
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
MAX_POSTS_PER_PROFILE = int(os.getenv("MAX_POSTS_PER_PROFILE", "3"))
MAX_COMMENTS_PER_POST = int(os.getenv("MAX_COMMENTS_PER_POST", "50"))
INSTAGRAM_LOGIN_URL = "https://www.instagram.com/accounts/login/"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class IdentityManager:
    """Gerencia a rotação de contas e detecção de saúde das sessões."""
    def __init__(self):
        self.current_account: Optional[Dict] = None

    async def get_next_available_account(self) -> Optional[Dict]:
        """Busca a próxima conta ativa, priorizando a menos usada."""
        try:
            res = supabase.table('scraping_accounts')\
                .select('*')\
                .eq('status', 'ACTIVE')\
                .order('last_used_at', desc=False)\
                .limit(1)\
                .execute()
            
            if res.data:
                self.current_account = res.data[0]
                return self.current_account
            
            if IG_USER and IG_PASS:
                logger.debug("⚠️ [Identity] Nenhuma conta no DB. Usando fallback do .env.")
                return {
                    'id': 'env_fallback',
                    'username': IG_USER,
                    'password': IG_PASS,
                    'session_id': INSTAGRAM_SESSIONID
                }
            return None
        except Exception as e:
            logger.debug(f"❌ [Identity] Erro ao buscar conta: {e}")
            return None

    async def mark_blocked(self, account_id: str):
        if account_id == 'env_fallback': return
        try:
            supabase.table('scraping_accounts').update({'status': 'BLOCKED'}).eq('id', account_id).execute()
        except: pass

    async def mark_shadowbanned(self, account_id: str):
        if account_id == 'env_fallback': return
        print(f"👻 [Identity] Conta {account_id} detectada com SHADOWBAN!")
        try:
            supabase.table('scraping_accounts').update({'status': 'SHADOWBANNED'}).eq('id', account_id).execute()
        except: pass

    async def update_usage(self, account_id: str, session_id: Optional[str] = None):
        if account_id == 'env_fallback': return
        data = {'last_used_at': datetime.now(timezone.utc).isoformat()}
        if session_id: data['session_id'] = session_id
        try:
            supabase.table('scraping_accounts').update(data).eq('id', account_id).execute()
        except: pass

from core.instagram_service import InstagramService

class InstagramHeadlessScraper:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.im = IdentityManager()
        self.active_account: Optional[Dict] = None
        self.service = InstagramService()

    def _log_kpi(self, tier_used: int, target: str, count: int, duration_ms: int, error: str = None):
        data = {
            'tier_used': tier_used,
            'alvo': target,
            'comentarios_coletados': count,
            'duracao_ms': duration_ms,
            'erro': error
        }
        try:
            supabase.table('kpi_runs').insert(data).execute()
        except Exception as e:
            logger.error(f"Erro ao registrar KPI: {e}")

    async def run(self, limit: int = 15, targets: List[Dict] = None, test_username: str = None, max_posts: int = None) -> List[Dict]:
        start_time = time.perf_counter()
        collected_comments: List[Dict] = []
        error = None

        try:
            logger.info("🧠 [Headless] Iniciando Instagram Headless Scraper (Service Mode)...")
            
            self.active_account = await self.im.get_next_available_account()
            if not self.active_account:
                error = "Nenhuma identidade disponível."
                logger.error(f"❌ [Headless] {error}")
                return collected_comments

            logger.info(f"👤 [Headless] Usando conta: @{self.active_account['username']}")

            async with async_playwright() as pw:
                self.playwright = pw
                self.browser = await pw.chromium.launch(
                    headless=PLAYWRIGHT_HEADLESS,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
                )
                context = await self.browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    locale="pt-BR",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )

                if self.active_account.get('session_id'):
                    await context.add_cookies([{'name': 'sessionid', 'value': self.active_account['session_id'], 'domain': '.instagram.com', 'path': '/'}])

                self.page = await context.new_page()
                self.page.set_default_timeout(60000)
                
                if await self._ensure_logged_in():
                    if not targets:
                        if test_username:
                            targets = [{'id': 1, 'username': test_username}]
                        else:
                            targets = self._load_pending_targets(limit)
                    
                    for candidate in targets:
                        username = candidate.get('username') if isinstance(candidate, dict) else candidate
                        if not username: continue
                        
                        # Delegação para o novo serviço unificado
                        result = await self.service.scrape_candidate_comments(
                            self.page, 
                            username, 
                            max_posts=max_posts or MAX_POSTS_PER_PROFILE
                        )
                        
                        if result:
                            # Sanitização básica e limpeza
                            for c in result:
                                c["texto_bruto"] = clean_comment(c.get("texto_bruto", ""), username)
                                c["tier_used"] = 4 # Headless
                            
                            valid_comments = [c for c in result if c.get("texto_bruto")]
                            collected_comments.extend(valid_comments)
                            
                            # Persistência imediata
                            self._persist_comments(valid_comments)
                            
                            # Update candidate metadata if needed (simplificado agora)
                            try:
                                supabase.table('candidatos').update({
                                    'last_scraped_at': datetime.now(timezone.utc).isoformat()
                                }).eq('username', username).execute()
                            except: pass
                
                await self.im.update_usage(self.active_account['id'])
                await self.browser.close()
                
        except Exception as e:
            error = str(e)
            logger.error(f"💥 [Headless] Erro no run: {error}")
        finally:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            target_str = ",".join([t['username'] if isinstance(t, dict) else str(t) for t in (targets or [])])
            self._log_kpi(4, target_str, len(collected_comments), duration_ms, error)

        return collected_comments

    def _persist_comments(self, comments: List[Dict]):
        """Persiste comentários no Supabase."""
        for c in comments:
            try:
                # Sanitização de campos para o DB
                data = {
                    "candidato_id": c.get("candidato_id"),
                    "post_shortcode": c.get("post_shortcode"),
                    "id_externo": str(c.get("id_externo")),
                    "texto_bruto": c.get("texto_bruto"),
                    "autor_username": c.get("autor_username"),
                    "data_publicacao": c.get("data_publicacao"),
                    "data_coleta": c.get("data_coleta"),
                    "plataforma": "INSTAGRAM",
                    "processado_ia": False,
                    "tier_used": c.get("tier_used", 4)
                }
                # Upsert utilizando a restrição única definida no SQL
                supabase.table('comentarios').upsert(data, on_conflict='candidato_id,post_shortcode,id_externo').execute()
            except Exception as e:
                logger.error(f"Erro na persistência (Upsert): {e}")

    async def _ensure_logged_in(self) -> bool:
        try:
            await self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            await asyncio.sleep(5)
            if "/accounts/login/" not in self.page.url: return True
            
            logger.info(f"🔑 [Headless] Tentando login para @{self.active_account['username']}...")
            await self.page.goto(INSTAGRAM_LOGIN_URL)
            await self.page.fill('input[name="username"]', self.active_account['username'])
            await self.page.fill('input[name="password"]', self.active_account['password'])
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state("networkidle")
            return "/accounts/login/" not in self.page.url
        except: return False

    def _load_pending_targets(self, limit: int) -> List[Dict]:
        res = supabase.table('candidatos').select('id,username').order('last_scraped_at', desc=False).limit(limit).execute()
        return res.data or []


if __name__ == '__main__':
    asyncio.run(InstagramHeadlessScraper().run())
