from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from playwright.async_api import Page, BrowserContext, async_playwright, Browser, TimeoutError as PlaywrightTimeoutError

from core.ai_service import ai_service

logger = logging.getLogger("instagram_scraper_v2")

@dataclass
class Session:
    label: str
    session_id: str
    blocked: bool = False
    error_count: int = 0
    last_used: Optional[datetime] = None

class InstagramScraperV2:
    """
    Motor de raspagem do Instagram independente (PASA v85.10).
    Focado em Playwright puro, sem Zyte.
    Implementa rotação de sessões, backoff exponencial e Stealth Mode Avançado.
    """

    def __init__(self, headless: bool = True, max_retries: int = 3, db_client: Optional[Any] = None, shutdown_event: Optional[asyncio.Event] = None):
        self.headless = headless
        self.max_retries = max_retries
        self.db = db_client 
        self.shutdown_event = shutdown_event 
        self.sessions: List[Session] = self._load_sessions()
        self.current_session_idx = 0
        self.captured_data: List[Dict[str, Any]] = []
        self.stats = {
            "posts_found": 0,
            "posts_scraped": 0,
            "comments_extracted": 0,
            "api_calls": 0,
            "browser_renders": 0,
            "session_rotations": 0,
            "junk_detected": 0,
            "errors": 0
        }

    def _load_sessions(self) -> List[Session]:
        """Carrega sessões das variáveis de ambiente."""
        sessions = []
        for i in range(1, 11):
            sid = os.getenv(f"INSTAGRAM_SESSIONID_{i}") or (os.getenv("INSTAGRAM_SESSIONID") if i == 1 else None)
            if sid:
                sessions.append(Session(label=f"SESSION_{i}", session_id=sid))
        
        sid_val = os.getenv("INSTAGRAM_SESSIONID_VAL")
        if sid_val:
            sessions.append(Session(label="SESSION_VAL", session_id=sid_val))

        cookie_full = os.getenv("INSTAGRAM_COOKIE_FULL")
        if cookie_full and "sessionid=" in cookie_full:
            sid = re.search(r'sessionid=([^;]+)', cookie_full)
            if sid:
                sessions.append(Session(label="COOKIE_FULL", session_id=sid.group(1)))

        logger.info(f"🔑 [V2] {len(sessions)} sessões carregadas.")
        return sessions

    def _get_next_session(self) -> Session:
        """Rotaciona para a próxima sessão disponível."""
        available = [s for s in self.sessions if not s.blocked]
        if not available:
            logger.error("❌ [V2] Todas as sessões estão bloqueadas!")
            raise RuntimeError("all_sessions_blocked")
        
        session = available[self.current_session_idx % len(available)]
        self.current_session_idx += 1
        return session

    async def _handle_response(self, response):
        """Interceptador de rede para capturar JSONs de interesse."""
        url = response.url
        if "graphql" in url or "comments" in url or "web_profile_info" in url:
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.captured_data.append({"url": url, "data": data})
                    self.stats["api_calls"] += 1
            except Exception:
                pass

    def _generate_stealth_profile(self) -> Dict[str, Any]:
        """Gera perfis de dispositivos e cabeçalhos HTTP realistas e aleatórios (PASA v85.10)."""
        chrome_major = random.choice([122, 123, 124, 125])
        chrome_build = random.randint(5000, 6400)
        chrome_patch = random.randint(100, 200)
        chrome_ver = f"{chrome_major}.0.{chrome_build}.{chrome_patch}"

        firefox_ver = f"{random.choice([124, 125, 126])}.0"
        safari_ver = f"17.{random.choice([3, 4, 5])}"

        os_templates = [
            # Windows Chrome
            {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
                "w": random.choice([1920, 1366, 1536, 1440, 1600]),
                "h": random.choice([1080, 768, 864, 900, 1200]),
                "platform": "Win32",
                "vendor": "Google Inc."
            },
            # Edge no Windows
            {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{chrome_major}.0.0.0",
                "w": 1920,
                "h": 1080,
                "platform": "Win32",
                "vendor": "Google Inc."
            },
            # macOS Chrome
            {
                "ua": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
                "w": random.choice([1440, 1680, 2560, 2880]),
                "h": random.choice([900, 1050, 1600, 1800]),
                "platform": "MacIntel",
                "vendor": "Google Inc."
            },
            # macOS Safari
            {
                "ua": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_ver} Safari/605.1.15",
                "w": 1440,
                "h": 900,
                "platform": "MacIntel",
                "vendor": "Apple Computer, Inc."
            },
            # iPhone iOS Safari
            {
                "ua": f"Mozilla/5.0 (iPhone; CPU iPhone OS 17_{random.choice([3,4,5])} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/605.1",
                "w": random.choice([390, 393, 428, 430]),
                "h": random.choice([844, 852, 926, 932]),
                "platform": "iPhone",
                "vendor": "Apple Computer, Inc."
            },
            # Android Chrome
            {
                "ua": f"Mozilla/5.0 (Linux; Android 14; Pixel {random.choice([7, 8])}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
                "w": 412,
                "h": 915,
                "platform": "Linux armv8l",
                "vendor": "Google Inc."
            }
        ]

        profile = random.choice(os_templates)

        headers = {
            "Accept-Language": random.choice([
                "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "pt-BR,pt;q=0.9,en-US;q=0.9",
                "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"
            ]),
            "Sec-Ch-Ua": f'"{chrome_major}";v="{chrome_major}", "Not(A:Brand";v="24", "Chromium";v="{chrome_major}"',
            "Sec-Ch-Ua-Mobile": "?1" if "Mobile" in profile["ua"] else "?0",
            "Sec-Ch-Ua-Platform": f'"{profile["platform"]}"',
            "Upgrade-Insecure-Requests": "1"
        }

        return {
            "ua": profile["ua"],
            "w": profile["w"],
            "h": profile["h"],
            "platform": profile["platform"],
            "vendor": profile["vendor"],
            "headers": headers
        }

    async def scrape_profile(self, username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50, max_age_days: int = 7) -> List[Dict[str, Any]]:
        """Extrai comentários de um perfil com retry e rotação."""
        all_comments = []
        retry_count = 0
        
        while retry_count < self.max_retries:
            session = self._get_next_session()
            if not session:
                break

            try:
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(
                        headless=self.headless,
                        args=[
                            "--disable-blink-features=AutomationControlled", 
                            "--no-sandbox",
                            "--disable-infobars",
                            "--window-position=0,0",
                            "--ignore-certificate-errors",
                            "--disable-extensions",
                            "--disable-notifications"
                        ]
                    )
                    
                    # 🎭 ROTAÇÃO DE STEALTH AMPLIADA (PASA v85.10)
                    profile = self._generate_stealth_profile()
                    
                    proxy_url = os.getenv("PROXY_URL")
                    context_kwargs = {
                        "viewport": {"width": profile["w"], "height": profile["h"]},
                        "user_agent": profile["ua"],
                        "extra_http_headers": profile["headers"],
                        "device_scale_factor": random.choice([1, 2, 3]),
                        "has_touch": "Mobile" in profile["ua"]
                    }
                    if proxy_url:
                        context_kwargs["proxy"] = {"server": proxy_url}
                        
                    context = await browser.new_context(**context_kwargs)
                    
                    # 🧪 INJEÇÃO DE STEALTH SCRIPTS (Fingerprint Bypass)
                    await context.add_init_script(f"""
                        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                        Object.defineProperty(navigator, 'platform', {{ get: () => '{profile["platform"]}' }});
                        Object.defineProperty(navigator, 'vendor', {{ get: () => '{profile["vendor"]}' }});
                        // Emula Plugins
                        Object.defineProperty(navigator, 'plugins', {{ get: () => [1, 2, 3, 4, 5] }});
                    """)
                    
                    await context.add_cookies([{
                        'name': 'sessionid', 
                        'value': session.session_id, 
                        'domain': '.instagram.com', 
                        'path': '/'
                    }])

                    page = await context.new_page()
                    page.on("response", self._handle_response)
                    
                    proxy_log = "com Proxy" if proxy_url else "sem Proxy"
                    logger.info(f"🎯 [V2] Scrape @{username} usando {session.label} | Profile: {profile['platform']} | Res: {profile['w']}x{profile['h']} ({proxy_log})")
                    
                    # 🛡️ VERIFICAÇÃO DE SESSÃO ATIVA (PASA v70.4)
                    if not await self._verify_session(page, session):
                        logger.warning(f"⚠️ [V2] Sessão {session.label} expirada ou inválida. Rotacionando...")
                        session.blocked = True
                        retry_count += 1
                        await browser.close()
                        continue

                    # 1. Navega para o Perfil
                    response = await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
                    
                    # 🛡️ PROTEÇÃO CONTRA 429
                    if response and response.status == 429:
                        logger.warning(f"⚠️ [V2] Erro 429 detectado. Rotacionando IP/Sessão...")
                        await context.clear_cookies()
                        await browser.close()
                        retry_count += 1
                        continue

                    # Check 404
                    try:
                        error_header = await page.query_selector("h2")
                        if error_header:
                            header_text = await error_header.inner_text()
                            if "Página não disponível" in header_text or "Sorry, this page" in header_text:
                                logger.error(f"❌ [V2] Alvo @{username} inexistente (404).")
                                await browser.close()
                                raise ValueError(f"invalid_target: 404_not_found")
                    except ValueError as ve: raise ve
                    except: pass

                    # Jitter de navegação inicial
                    await asyncio.sleep(random.uniform(4, 8))

                    if "login" in page.url:
                        logger.warning(f"⚠️ [V2] Login wall detectado para {session.label}")
                        session.blocked = True
                        retry_count += 1
                        await browser.close()
                        continue

                    # Extrai metadados dos posts
                    post_metas = await self._extract_shortcodes(page, max_posts)
                    self.stats["posts_found"] = len(post_metas)
                    
                    scraped_count = 0
                    consecutive_old_posts = 0
                    
                    for meta in post_metas:
                        if self.shutdown_event and self.shutdown_event.is_set():
                            logger.warning(f"🛑 [V2] Interrupção detectada! Abortando...")
                            break

                        if scraped_count >= max_posts:
                            break
                            
                        shortcode = meta["shortcode"]
                        if page.is_closed(): break

                        is_pinned = meta["is_pinned"]
                        post_timestamp = meta.get("timestamp")
                        
                        if is_pinned:
                            logger.info(f"⏭️ [V2] Post {shortcode} FAST-SKIP (Fixado).")
                            continue

                        # Fast-Skip Temporal
                        if post_timestamp:
                            try:
                                post_dt = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00'))
                                age_days = (datetime.now(timezone.utc) - post_dt).days
                                if age_days > max_age_days:
                                    consecutive_old_posts += 1
                                    logger.info(f"⏳ [V2] Post {shortcode} é velho ({age_days}d). [{consecutive_old_posts}/3]")
                                    if consecutive_old_posts >= 3: break
                                    continue
                                else:
                                    consecutive_old_posts = 0
                            except: pass

                        logger.info(f"📄 [V2] Verificando post {shortcode}...")
                        post_comments = await self._scrape_post(page, shortcode, username, candidato_id, max_comments_per_post, max_age_days)
                        
                        if post_comments:
                            all_comments.extend(post_comments)
                            scraped_count += 1
                            self.stats["posts_scraped"] += 1
                            # Jitter entre posts (Simulação Humana)
                            await asyncio.sleep(random.uniform(6, 18))
                        else:
                            logger.info(f"⏭️ [V2] Post {shortcode} ignorado.")

                    await browser.close()
                    logger.info(f"✅ [V2] @{username} finalizado. {len(all_comments)} comentários extraídos.")
                    return {
                        "comments": all_comments,
                        "post_metas": post_metas
                    }

            except Exception as e:
                logger.error(f"💥 [V2] Erro na tentativa {retry_count+1}: {e}")
                self.stats["errors"] += 1
                retry_count += 1
                await asyncio.sleep((2 ** retry_count) + random.uniform(2, 5))

        return {"comments": all_comments, "post_metas": []}

    async def open_post_modal(self, page: Page, shortcode: str) -> bool:
        """Abre um post com bypass de interceptação."""
        if page.is_closed(): return False
        
        selector = f'a[href*="/{shortcode}/"]'
        try:
            post_element = await page.query_selector(selector)
            if post_element:
                await post_element.click(timeout=15000, force=True)
                await asyncio.sleep(random.uniform(4, 7))
                if await page.query_selector("article"): return True
        except: pass

        # Fallback URL
        try:
            logger.info(f"🔄 [V2] Fallback URL para {shortcode}...")
            await page.goto(f"https://www.instagram.com/p/{shortcode}/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(5, 8))
            if await page.query_selector("article") or len(await page.query_selector_all("section")) > 0:
                return True
        except: pass
        
        return False

    async def scroll_comment_column(self, page: Page, scroll_amount: int = 800) -> None:
        """Emula scroll de mouse realista."""
        # Move para o lado direito do modal onde os comentários geralmente ficam
        await page.mouse.move(random.randint(800, 1200), random.randint(300, 600))
        await page.mouse.wheel(0, scroll_amount + random.randint(-100, 100))
        await asyncio.sleep(random.uniform(2, 4))

    async def close_post_modal(self, page: Page) -> None:
        """Fecha o modal de forma limpa."""
        if page.is_closed(): return
        try:
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)
            if await page.query_selector("article"):
                await page.go_back(wait_until="domcontentloaded", timeout=10000)
        except: pass

    async def _scrape_post(self, page: Page, shortcode: str, username: str, candidato_id: str, max_comments: int, max_age_days: int) -> List[Dict[str, Any]]:
        """Extrai comentários de um post."""
        self.captured_data = []
        if page.is_closed(): return []
        if not await self.open_post_modal(page, shortcode): return []

        # Verificação de Idade
        post_date_iso = await page.evaluate("() => document.querySelector('article time')?.getAttribute('datetime')")
        if post_date_iso:
            post_dt = datetime.fromisoformat(post_date_iso.replace('Z', '+00:00'))
            if (datetime.now(timezone.utc) - post_dt).days > max_age_days:
                await self.close_post_modal(page)
                return []

        # Scrolls Realistas
        for _ in range(random.randint(2, 4)):
            await self.scroll_comment_column(page, scroll_amount=random.randint(1000, 1500))
        
        comments = self._parse_captured_json(shortcode)
        if not comments: comments = await self._extract_from_scripts(page, shortcode)
        if not comments: comments = await self._extract_from_dom(page, shortcode)

        await self.close_post_modal(page)
        
        now = datetime.now(timezone.utc).isoformat()
        normalized = []
        junk_patterns = ['também da meta', 'instagram lite', 'localizações', 'campanha 2201', 'áudio original']
        
        for c in comments[:max_comments]:
            texto = (c.get("texto_bruto") or c.get("texto", "")).replace("\u0000", "").strip()
            if len(texto) < 2 or len(texto) > 2000: continue
            if any(p in texto.lower() for p in junk_patterns): continue
            
            normalized.append({
                "id_externo": str(c.get("id_externo", f"v2_{shortcode}_{random.randint(0, 999999)}")),
                "texto_bruto": texto,
                "autor_username": c.get("autor_username") or c.get("autor", "unknown"),
                "data_publicacao": c.get("data_publicacao") or c.get("timestamp") or post_date_iso or now,
                "data_coleta": now,
                "candidato_id": username,
                "post_shortcode": shortcode,
                "plataforma": "INSTAGRAM",
                "processado_ia": False,
                "tier_used": 2
            })
        
        return normalized

    async def _extract_shortcodes(self, page: Page, limit: int) -> List[Dict[str, Any]]:
        """Extrai shortcodes do grid."""
        return await page.evaluate(f"""
            () => {{
                const results = [];
                const posts = document.querySelectorAll('div._aabd, div._ac7v div');
                posts.forEach(p => {{
                    const link = p.querySelector('a[href*="/p/"], a[href*="/reel/"]');
                    if (!link) return;
                    const match = link.href.match(/\\/(p|reel)\\/([^/]+)\\//);
                    if (!match) return;
                    const shortcode = match[2];
                    if (results.some(r => r.shortcode === shortcode)) return;
                    results.push({{ 
                        shortcode, 
                        is_pinned: !!p.querySelector('svg[aria-label*="Pinned"], svg[aria-label*="Fixado"]'),
                        timestamp: p.querySelector('time')?.getAttribute('datetime') 
                    }});
                }});
                return results.slice(0, {limit + 3});
            }}
        """)

    def _parse_captured_json(self, shortcode: str) -> List[Dict[str, Any]]:
        comments = []
        for item in self.captured_data:
            extracted = self._recursive_find_comments(item["data"])
            if extracted: comments.extend(extracted)
        return comments

    async def _extract_from_scripts(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        script_contents = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script[type="application/json"]'))
                .map(s => s.innerText).filter(txt => txt.includes('comment'))
        """)
        comments = []
        for content in script_contents:
            try:
                extracted = self._recursive_find_comments(json.loads(content))
                comments.extend(extracted)
            except: continue
        return comments

    async def _extract_from_dom(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        """Heurística baseada em h3 (estilo moderno IG)."""
        return await page.evaluate("""
            () => {
                const results = [];
                const h3s = Array.from(document.querySelectorAll('article h3'));
                h3s.forEach(h => {
                    const username = h.innerText.trim();
                    if (!username || username.includes(' ')) return;
                    let node = h;
                    for(let i = 0; i < 6; i++) { if(node.parentElement) node = node.parentElement; }
                    const spans = Array.from(node.querySelectorAll('span[dir="auto"]'));
                    for(let span of spans) {
                        const txt = span.innerText.trim();
                        if (txt && txt !== username && txt.length > 2) {
                            results.push({ autor: username, texto: txt });
                            break;
                        }
                    }
                });
                return results;
            }
        """)

    def _recursive_find_comments(self, data: Any) -> List[Dict[str, Any]]:
        comments = []
        if isinstance(data, dict):
            if "edge_media_to_parent_comment" in data:
                for edge in data["edge_media_to_parent_comment"].get("edges", []):
                    node = edge.get("node", {})
                    comments.append({
                        "id_externo": f"ig_{node.get('id')}",
                        "texto": node.get("text"),
                        "autor": node.get("owner", {}).get("username"),
                        "timestamp": datetime.fromtimestamp(node.get("created_at", 0), timezone.utc).isoformat()
                    })
            elif "xdt_api__v1__media__shortcode__web_info" in data:
                for item in data["xdt_api__v1__media__shortcode__web_info"].get("items", []):
                    for c in item.get("preview_comments", []):
                        comments.append({
                            "id_externo": f"ig_{c.get('pk')}", "texto": c.get("text"),
                            "autor": c.get("user", {}).get("username"),
                            "timestamp": datetime.fromtimestamp(c.get("created_at", 0), timezone.utc).isoformat()
                        })
            for v in data.values(): comments.extend(self._recursive_find_comments(v))
        elif isinstance(data, list):
            for item in data: comments.extend(self._recursive_find_comments(item))
        return comments

    async def _verify_session(self, page: Page, session: Session) -> bool:
        try:
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(3)
            return "accounts/login" not in page.url
        except: return False

    async def _take_screenshot(self, page: Page, name: str) -> None:
        try:
            if page.is_closed(): return
            folder = os.path.join("logs", "evidence")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{datetime.now().strftime('%H%M%S')}_{name}.png")
            await page.screenshot(path=path, full_page=True)
        except: pass

async def scrape_instagram(username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50) -> List[Dict[str, Any]]:
    scraper = InstagramScraperV2()
    return await scraper.scrape_profile(username, candidato_id, max_posts, max_comments_per_post)
