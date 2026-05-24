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
    Motor de raspagem do Instagram independente (PASA v52.0).
    Focado em Playwright puro, sem Zyte.
    Implementa rotação de sessões, backoff exponencial e extração multi-camada.
    """

    def __init__(self, headless: bool = True, max_retries: int = 3):
        self.headless = headless
        self.max_retries = max_retries
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
            "errors": 0
        }

    def _load_sessions(self) -> List[Session]:
        """Carrega sessões das variáveis de ambiente."""
        sessions = []
        # Opção 1: SessionIDs múltiplos
        for i in range(1, 11):
            sid = os.getenv(f"INSTAGRAM_SESSIONID_{i}") or (os.getenv("INSTAGRAM_SESSIONID") if i == 1 else None)
            if sid:
                sessions.append(Session(label=f"SESSION_{i}", session_id=sid))
        
        # Opção 2: Cookie completo (converte para sessionid se possível)
        cookie_full = os.getenv("INSTAGRAM_COOKIE_FULL")
        if cookie_full and "sessionid=" in cookie_full:
            sid = re.search(r'sessionid=([^;]+)', cookie_full)
            if sid:
                sessions.append(Session(label="COOKIE_FULL", session_id=sid.group(1)))

        logger.info(f"🔑 [V2] {len(sessions)} sessões carregadas.")
        return sessions

    def _get_next_session(self) -> Session:
        """Rotaciona para a próxima sessão disponível. Levanta erro se todas estiverem bloqueadas."""
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

    async def scrape_profile(self, username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50) -> List[Dict[str, Any]]:
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
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                    )
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    )
                    
                    await context.add_cookies([{
                        'name': 'sessionid', 
                        'value': session.session_id, 
                        'domain': '.instagram.com', 
                        'path': '/'
                    }])

                    page = await context.new_page()
                    page.on("response", self._handle_response)
                    
                    logger.info(f"🎯 [V2] Scrape @{username} usando {session.label} (Tentativa {retry_count+1})")
                    
                    # 1. Perfil
                    await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(random.uniform(5, 10)) # Cooldown space inicial maior
                    
                    if "login" in page.url:
                        logger.warning(f"⚠️ [V2] Login wall detectado para {session.label}")
                        session.blocked = True
                        self.stats["session_rotations"] += 1
                        retry_count += 1
                        await browser.close()
                        continue

                    # Extrai shortcodes
                    shortcodes = await self._extract_shortcodes(page, max_posts)
                    self.stats["posts_found"] = len(shortcodes)
                    
                    for code in shortcodes:
                        post_comments = await self._scrape_post(page, code, username, candidato_id, max_comments_per_post)
                        all_comments.extend(post_comments)
                        self.stats["posts_scraped"] += 1
                        # Jitter agressivo entre posts (PASA v52.0)
                        await asyncio.sleep(random.uniform(5, 15)) 

                    await browser.close()
                    logger.info(f"✅ [V2] @{username} finalizado. {len(all_comments)} comentários extraídos.")
                    return all_comments

            except Exception as e:
                logger.error(f"💥 [V2] Erro na tentativa {retry_count+1}: {e}")
                self.stats["errors"] += 1
                retry_count += 1
                # Backoff exponencial com jitter
                wait = (2 ** retry_count) + random.uniform(2, 5)
                await asyncio.sleep(wait)

        return all_comments

    async def _scrape_post(self, page: Page, shortcode: str, username: str, candidato_id: str, max_comments: int) -> List[Dict[str, Any]]:
        """Extrai comentários de um post específico clicando no elemento do perfil para abrir o modal."""
        self.captured_data = []
        
        try:
            # Encontra o elemento do post correspondente ao shortcode no feed
            selector = f'a[href*="/{shortcode}/"]'
            post_element = await page.query_selector(selector)
            
            if not post_element:
                logger.warning(f"⚠️ [V2] Elemento do post {shortcode} não encontrado no feed.")
                return []
                
            # Clica no post para abrir o modal
            await post_element.click()
            await asyncio.sleep(random.uniform(5, 7)) # Aguarda abertura e requisições iniciais
            
            # Move o mouse para a área lateral direita do modal (onde ficam os comentários) e rola
            await page.mouse.move(1000, 400)
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(3)
            
            # Camada 1: Network Interception (Mais rico)
            comments = self._parse_captured_json(shortcode)
            
            # Camada 2: Fallback Scripts (data-sjs)
            if not comments:
                comments = await self._extract_from_scripts(page, shortcode)
            
            # Camada 3: Fallback DOM (Robusto)
            if not comments:
                self.stats["browser_renders"] += 1
                comments = await self._extract_from_dom(page, shortcode)

            # Fecha o modal usando a tecla Escape
            await page.keyboard.press("Escape")
            await asyncio.sleep(random.uniform(2, 3)) # Espera fechamento
            
            # Normalização final
            now = datetime.now(timezone.utc).isoformat()
            normalized = []
            for c in comments[:max_comments]:
                normalized.append({
                    "id_externo": str(c.get("id_externo", f"v2_{shortcode}_{random.randint(0, 999999)}")),
                    "texto_bruto": c.get("texto_bruto") or c.get("texto", ""),
                    "autor_username": c.get("autor_username") or c.get("autor", "unknown"),
                    "data_publicacao": c.get("data_publicacao") or c.get("timestamp") or now,
                    "data_coleta": now,
                    "candidato_id": username, # Mapeado para o username conforme padrão STATE.md
                    "post_shortcode": shortcode,
                    "plataforma": "INSTAGRAM",
                    "processado_ia": False,
                    "tier_used": 2 # V2 engine
                })
            
            self.stats["comments_extracted"] += len(normalized)
            return normalized

        except Exception as e:
            logger.error(f"⚠️ [V2] Falha ao processar post {shortcode} via modal: {e}")
            # Tenta fechar o modal como contingência em caso de erro
            try:
                await page.keyboard.press("Escape")
            except:
                pass
            return []

    async def _extract_shortcodes(self, page: Page, limit: int) -> List[str]:
        return await page.evaluate(f"""
            () => Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]'))
                .map(a => {{
                    const match = a.href.match(/\\/(p|reel)\\/([^/]+)\\//);
                    return match ? match[2] : null;
                }})
                .filter(Boolean)
                .slice(0, {limit})
        """)

    def _parse_captured_json(self, shortcode: str) -> List[Dict[str, Any]]:
        """Procura comentários nos JSONs interceptados."""
        comments = []
        for item in self.captured_data:
            data = item["data"]
            extracted = self._recursive_find_comments(data)
            if extracted:
                comments.extend(extracted)
        return comments

    async def _extract_from_scripts(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        script_contents = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script[type="application/json"]'))
                .map(s => s.innerText)
                .filter(txt => txt.includes('comment') || txt.includes('xdt_'))
        """)
        comments = []
        for content in script_contents:
            try:
                data = json.loads(content)
                extracted = self._recursive_find_comments(data)
                comments.extend(extracted)
            except: continue
        return comments

    async def _extract_from_dom(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        """Heurística baseada em spans dir=auto (PASA v51.0 upgrade)."""
        return await page.evaluate("""
            () => {
                const results = [];
                const spans = Array.from(document.querySelectorAll('span[dir="auto"]'));
                const blacklist = ['explorar', 'explore', 'messages', 'notificações', 'notifications', 
                                 'create', 'dashboard', 'perfil', 'profile', 'mais', 'more',
                                 'responder', 'reply', 'search', 'pesquisa', 'reels', 'home', 'threads'];

                let lastUsername = "";
                for (let i = 0; i < spans.length; i++) {
                    const txt = spans[i].innerText.trim();
                    if (!txt || txt.length < 2) continue;
                    
                    const isUsername = /^[a-z0-9._]{3,30}$/i.test(txt) && !txt.includes(' ') && !blacklist.includes(txt.toLowerCase());
                    
                    if (isUsername) {
                        lastUsername = txt;
                    } else if (lastUsername && !/^[0-9]+[ ]?[hdm]$/i.test(txt) && !blacklist.some(b => txt.toLowerCase().includes(b))) {
                        results.push({ autor: lastUsername, texto: txt });
                        lastUsername = ""; 
                    }
                }
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
                            "id_externo": f"ig_{c.get('pk')}",
                            "texto": c.get("text"),
                            "autor": c.get("user", {}).get("username"),
                            "timestamp": datetime.fromtimestamp(c.get("created_at", 0), timezone.utc).isoformat()
                        })
            for v in data.values():
                comments.extend(self._recursive_find_comments(v))
        elif isinstance(data, list):
            for item in data:
                comments.extend(self._recursive_find_comments(item))
        return comments

    def get_stats(self) -> Dict[str, Any]:
        return self.stats

async def scrape_instagram(username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50) -> List[Dict[str, Any]]:
    """Função utilitária rápida."""
    scraper = InstagramScraperV2()
    return await scraper.scrape_profile(username, candidato_id, max_posts, max_comments_per_post)
