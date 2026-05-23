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

class InstagramHeadlessScraper:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.im = IdentityManager()
        self.active_account: Optional[Dict] = None

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

    async def _check_cooldown(self, username: str) -> bool:
        """Verifica se o alvo está em cooldown."""
        res = supabase.table('alvo_backoff').select('next_allowed_at').eq('candidato_id', username).execute()
        if res.data:
            next_allowed = datetime.fromisoformat(res.data[0]['next_allowed_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) < next_allowed:
                return True
        return False

    async def _apply_backoff(self, username: str):
        """Aplica backoff exponencial com jitter."""
        res = supabase.table('alvo_backoff').select('strikes').eq('candidato_id', username).execute()
        strikes = res.data[0]['strikes'] + 1 if res.data else 1

        # Backoff: 5m, 15m, 45m, 3h... até 12h max
        base_minutes = [5, 15, 45, 180, 720]
        idx = min(strikes - 1, len(base_minutes) - 1)
        minutes = base_minutes[idx]

        # Jitter +/- 20%
        jitter = minutes * 0.2
        wait_minutes = minutes + random.uniform(-jitter, jitter)

        next_allowed = datetime.now(timezone.utc) + timedelta(minutes=wait_minutes)

        supabase.table('alvo_backoff').upsert({
            'candidato_id': username,
            'strikes': strikes,
            'next_allowed_at': next_allowed.isoformat()
        }).execute()
        logger.warning(f"⏳ Alvo {username} em cooldown até {next_allowed} (strike {strikes})")

    async def _is_profile_not_found(self) -> bool:
        """Verifica se a página atual indica perfil inexistente."""
        try:
            content = await self.page.content()
            return "Página não disponível" in content or "Sorry, this page" in content
        except Exception:
            return False

    async def run(self, limit: int = 15, targets: List[Dict] = None, test_username: str = None) -> List[Dict]:
        start_time = time.perf_counter()
        total_comments = 0
        error = None
        
        collected_comments: List[Dict] = []

        try:
            logger.info("🧠 [Headless] Iniciando Instagram Headless Scraper (Rotation Mode)...")
            
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
                        result = await self._scrape_candidate(candidate)
                        if result is None:
                            error = f"Possível Shadowban ou Bloqueio na conta @{self.active_account['username']}"
                            logger.warning(f"⚠️ [Headless] {error}")
                            await self.im.mark_shadowbanned(self.active_account['id'])
                            break
                        if isinstance(result, list):
                            collected_comments.extend(result)
                
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

    async def _ensure_logged_in(self) -> bool:
        try:
            await self.page.goto("https://www.instagram.com/", wait_until="commit")
            await asyncio.sleep(5)
            if "/accounts/login/" not in self.page.url: return True
            
            print(f"🔑 [Headless] Tentando login para @{self.active_account['username']}...")
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

    async def _has_session_cookie(self) -> bool:
        assert self.page is not None
        cookies = await self.page.context.cookies()
        return any(cookie.get('name') == 'sessionid' and cookie.get('value') for cookie in cookies)



    async def _scrape_candidate(self, candidate: Any) -> Optional[List[Dict]]:
        if isinstance(candidate, str):
            username = candidate
        else:
            username = candidate.get('username')
            
        if not username:
            return None
            
        logger.info(f"🎯 [Headless] @{username}...")
        try:
            await self.page.goto(f"https://www.instagram.com/{username}/", timeout=60000)
            await asyncio.sleep(3)

            if await self._is_profile_not_found():
                logger.warning(f"❌ [Headless] Perfil @{username} não encontrado.")
                return []

            # Coleta shortcodes dos posts via DOM
            shortcodes = await self.page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]'))
                    .map(a => a.href.match(/\/(p|reel)\/([^/]+)\//)?.[2])
                    .filter(Boolean)
                    .slice(0, 3)
            """)

            comments: List[Dict] = []
            for shortcode in shortcodes:
                post_comments = await self._collect_post_comments(username, shortcode)
                comments.extend(post_comments)

            logger.info(f"✅ [Headless] @{username}: {len(comments)} comentários coletados")
            return comments
            
        except Exception as e:
            logger.error(f"❌ [Headless] Error scraping @{username}: {e}")
            return None

    async def _collect_post_comments(self, username: str, shortcode: str) -> List[Dict]:
        """Coleta comentários de um post específico via DOM."""
        try:
            await self.page.goto(f"https://www.instagram.com/p/{shortcode}/", timeout=60000)
            await asyncio.sleep(4)

            raw_comments = await self.page.evaluate("""
                () => Array.from(document.querySelectorAll('div.x9f619 span[dir="auto"], span._ap30'))
                    .map(el => el.innerText.trim())
                    .filter(txt => txt.length > 2)
            """)

            now = datetime.now(timezone.utc).isoformat()
            return [
                {
                    "id_externo": f"headless_{shortcode}_{i}",
                    "texto_bruto": text,
                    "autor_username": "unknown",
                    "data_publicacao": now,
                    "data_coleta": now,
                    "post_shortcode": shortcode,
                    "plataforma": "INSTAGRAM",
                    "rede_social": "INSTAGRAM",
                    "candidato_id": username,
                    "processado_ia": False,
                    "mined": True,
                }
                for i, text in enumerate(raw_comments[:MAX_COMMENTS_PER_POST])
            ]
        except Exception as e:
            logger.error(f"❌ [Headless] Erro ao coletar post {shortcode}: {e}")
            return []

    def _update_candidate_data(self, candidate_id: str, profile_data: Dict[str, Any]):
        """Update candidate data in database with profile information."""
        try:
            update_data = {
                'username': profile_data.get('username'),
                'full_name': profile_data.get('full_name'),
                'biography': profile_data.get('biography'),
                'follower_count': profile_data.get('follower_count'),
                'following_count': profile_data.get('following_count'),
                'media_count': profile_data.get('media_count'),
                'is_verified': profile_data.get('is_verified', False),
                'is_private': profile_data.get('is_private', False),
                'profile_pic_url': profile_data.get('profile_pic_url'),
                'external_url': profile_data.get('external_url'),
                'last_scraped_at': datetime.now(timezone.utc).isoformat()
            }
            
            supabase.table('candidatos').update(update_data).eq('id', candidate_id).execute()
            logger.info(f"📝 [Headless] Updated candidate data for {candidate_id}")
            
        except Exception as e:
            logger.error(f"❌ [Headless] Error updating candidate data: {e}")


    async def _scrape_post(self, username: str, shortcode: str):
        try:
            await self.page.goto(f"https://www.instagram.com/p/{shortcode}/")
            await asyncio.sleep(4)
            
            comments = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('div.x9f619 span[dir="auto"], span._ap30'))
                    .map(el => el.innerText.trim())
                    .filter(txt => txt.length > 2);
            }""")
            
            for cmd in comments[:MAX_COMMENTS_PER_POST]:
                self._save_comment(username, shortcode, cmd)
        except: pass

    def to_utc_iso(self, dt):
        if isinstance(dt, (int, float)):  # epoch
            return datetime.fromtimestamp(dt, tz=timezone.utc).isoformat()
        if isinstance(dt, str):
            return datetime.fromisoformat(dt.replace('Z', '+00:00')).astimezone(timezone.utc).isoformat()
        if isinstance(dt, datetime):
            return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _save_comment(self, username: str, shortcode: str, comment_data: Dict):
        valid_text = clean_comment(comment_data.get('text', ''), username)
        if not valid_text: return

        data = {
            'candidato_id': username, 
            'post_shortcode': shortcode,
            'id_externo': comment_data.get('id', 'unknown'),
            'autor_username': comment_data.get('ownerUsername', 'unknown'),
            'texto_bruto': valid_text, 
            'tier_used': 4, # Headless
            'like_count': 0, 
            'data_publicacao': self.to_utc_iso(comment_data.get('timestamp')),
            'data_coleta': self.to_utc_iso(None),
            'processado_ia': False
        }
        try: 
            # Upsert utilizando a restrição única definida no SQL
            supabase.table('comentarios')\
                .upsert(data, on_conflict='candidato_id,post_shortcode,id_externo')\
                .header('Prefer', 'return=representation, resolution=merge-duplicates')\
                .header('Content-Profile', 'public')\
                .execute()
        except Exception as e:
            logger.error(f"Erro na persistência (Upsert): {e}")

if __name__ == '__main__':
    asyncio.run(InstagramHeadlessScraper().run())
