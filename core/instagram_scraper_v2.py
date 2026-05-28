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
    Motor de raspagem do Instagram independente (PASA v52.0).
    Focado em Playwright puro, sem Zyte.
    Implementa rotação de sessões, backoff exponencial e extração multi-camada.
    """

    def __init__(self, headless: bool = True, max_retries: int = 3, db_client: Optional[Any] = None):
        self.headless = headless
        self.max_retries = max_retries
        self.db = db_client # Cliente Supabase para verificações inteligentes
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
        # Opção 1: SessionIDs múltiplos
        for i in range(1, 11):
            sid = os.getenv(f"INSTAGRAM_SESSIONID_{i}") or (os.getenv("INSTAGRAM_SESSIONID") if i == 1 else None)
            if sid:
                sessions.append(Session(label=f"SESSION_{i}", session_id=sid))
        
        # Opção 1.5: SessionID específico de validação (v84.6)
        sid_val = os.getenv("INSTAGRAM_SESSIONID_VAL")
        if sid_val:
            sessions.append(Session(label="SESSION_VAL", session_id=sid_val))

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

    def _generate_stealth_profile(self) -> Dict[str, Any]:
        """Gera perfis de dispositivos e cabeçalhos HTTP realistas e aleatórios (PASA v83.6)."""
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
                "w": random.choice([1920, 1366, 1536]),
                "h": random.choice([1080, 768, 864])
            },
            # Edge no Windows
            {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{chrome_major}.0.0.0",
                "w": 1920,
                "h": 1080
            },
            # Firefox no Windows
            {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{firefox_ver}) Gecko/20100101 Firefox/{firefox_ver}",
                "w": 1920,
                "h": 1080
            },
            # macOS Chrome
            {
                "ua": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
                "w": random.choice([1440, 1680, 2560]),
                "h": random.choice([900, 1050, 1600])
            },
            # macOS Safari
            {
                "ua": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_ver} Safari/605.1.15",
                "w": 1440,
                "h": 900
            },
            # Linux Chrome
            {
                "ua": f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
                "w": 1366,
                "h": 768
            },
            # iPhone iOS Safari
            {
                "ua": f"Mozilla/5.0 (iPhone; CPU iPhone OS 17_{random.choice([3,4,5])} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/605.1",
                "w": 390,
                "h": 844
            },
            # Android Chrome
            {
                "ua": f"Mozilla/5.0 (Linux; Android 14; Pixel {random.choice([7, 8])}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
                "w": 412,
                "h": 915
            }
        ]

        profile = random.choice(os_templates)

        headers = {
            "Accept-Language": random.choice([
                "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "pt-BR,pt;q=0.9,en-US;q=0.9",
                "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"
            ])
        }

        return {
            "ua": profile["ua"],
            "w": profile["w"],
            "h": profile["h"],
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
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                    )
                    
                    # 🎭 ROTAÇÃO DE STEALTH AMPLIADA (PASA v83.6)
                    profile = self._generate_stealth_profile()
                    
                    context = await browser.new_context(
                        viewport={"width": profile["w"], "height": profile["h"]},
                        user_agent=profile["ua"],
                        extra_http_headers=profile["headers"]
                    )
                    
                    await context.add_cookies([{
                        'name': 'sessionid', 
                        'value': session.session_id, 
                        'domain': '.instagram.com', 
                        'path': '/'
                    }])

                    page = await context.new_page()
                    page.on("response", self._handle_response)
                    
                    logger.info(f"🎯 [V2] Scrape @{username} usando {session.label} | Profile: {profile['ua'][:30]}... (Tentativa {retry_count+1})")
                    
                    # 🛡️ VERIFICAÇÃO DE SESSÃO ATIVA (PASA v70.4)
                    if not await self._verify_session(page, session):
                        logger.warning(f"⚠️ [V2] Sessão {session.label} expirada ou inválida. Rotacionando...")
                        session.blocked = True
                        retry_count += 1
                        await browser.close()
                        continue

                    # 1. Perfil
                    await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)

                    # Check imediato de erro 404 antes do sleep longo
                    try:
                        error_header = await page.query_selector("h2")
                        if error_header:
                            header_text = await error_header.inner_text()
                            if "Página não disponível" in header_text or "Sorry, this page" in header_text:
                                logger.error(f"❌ [V2] Alvo @{username} inexistente (404 detectado no H2).")
                                await self._take_screenshot(page, f"404_{username}")
                                await browser.close()
                                raise ValueError(f"invalid_target: 404_not_found")
                    except ValueError as ve: raise ve
                    except: pass

                    await asyncio.sleep(random.uniform(5, 10))

                    if "login" in page.url:
                        logger.warning(f"⚠️ [V2] Login wall detectado para {session.label}")
                        await self._take_screenshot(page, f"login_wall_{session.label}")
                        session.blocked = True
                        self.stats["session_rotations"] += 1
                        retry_count += 1
                        await browser.close()
                        continue

                    # 🛡️ VALIDAÇÃO BIOGRÁFICA (v64.0): IA verifica se a Bio condiz com o alvo
                    # validation = await self._validate_target_identity(page, username)
                    # if not validation["valid"]:
                    #    logger.error(f"❌ [V2] Alvo @{username} inválido: {validation['reason']}")
                    #    await browser.close()
                    #    raise ValueError(f"invalid_target: {validation['reason']}")
                    
                    # Chamada de IA para validar identidade
                    # bio_check = await ai_service.validate_identity(
                    #    expected_name=candidato_id, 
                    #    display_name=validation.get("display_name", ""),
                    #    bio=validation.get("biography", ""),
                    #    followers=validation.get("followers", "0"),
                    #    is_verified=validation.get("is_verified", False)
                    # )

                    # if not bio_check.get("is_authentic", True):
                    #    logger.error(f"🚫 [V2] ALVO INAUTÊNTICO DETECTADO: @{username}. Motivo: {bio_check.get('reason')}")
                    #    await browser.close()
                    #    raise ValueError(f"inauthentic_identity: {bio_check.get('reason')}")
                    
                    logger.info(f"✅ [V2] Validação de identidade pulada para @{username} (Modo YOLO).")

                    # Extrai metadados dos posts (shortcode + is_pinned)
                    post_metas = await self._extract_shortcodes(page, max_posts)
                    self.stats["posts_found"] = len(post_metas)
                    
                    scraped_count = 0
                    consecutive_old_posts = 0
                    
                    for meta in post_metas:
                        if scraped_count >= max_posts:
                            break
                            
                        shortcode = meta["shortcode"]
                        if page.is_closed():
                            logger.warning(f"⚠️ [V2] A página do navegador foi fechada antes de processar o post {shortcode}. Abortando o loop de posts.")
                            break

                        is_pinned = meta["is_pinned"]
                        post_timestamp = meta.get("timestamp")
                        
                        # 1. Skip de Fixados (v62.0)
                        if is_pinned:
                            logger.info(f"⏭️ [V2] Post {shortcode} FAST-SKIP (Fixado).")
                            continue

                        # 2. Fast-Skip Temporal (v62.1/v65.0): Verifica data diretamente do grid
                        if post_timestamp:
                            try:
                                post_dt = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00'))
                                age_days = (datetime.now(timezone.utc) - post_dt).days
                                if age_days > max_age_days:
                                    consecutive_old_posts += 1
                                    logger.info(f"⏳ [V2] Post {shortcode} é velho ({age_days}d). [{consecutive_old_posts}/3]")
                                    
                                    if consecutive_old_posts >= 3:
                                        logger.info(f"⏭️ [V2] Detectados 3 posts velhos seguidos em @{username}. Encerrando busca.")
                                        break
                                    continue # Tenta o próximo do grid
                                else:
                                    consecutive_old_posts = 0 # Reseta se encontrar um novo
                            except: pass

                        logger.info(f"📄 [V2] Verificando post {shortcode}...")
                        
                        # Processa o post
                        post_comments = await self._scrape_post(page, shortcode, username, candidato_id, max_comments_per_post, max_age_days)
                        
                        if page.is_closed():
                            logger.warning(f"⚠️ [V2] A página do navegador foi fechada durante o processamento do post {shortcode}. Abortando o loop de posts.")
                            break
                        
                        if post_comments:
                            all_comments.extend(post_comments)
                            scraped_count += 1
                            self.stats["posts_scraped"] += 1
                            # Jitter agressivo entre posts
                            await asyncio.sleep(random.uniform(5, 15))
                        else:
                            logger.info(f"⏭️ [V2] Post {shortcode} ignorado (velho, fixado já visto ou sem comentários).")
                            # Se o _scrape_post retornou vazio e não era fixado, pode ser por idade detectada lá
                            # Mas aqui já temos a verificação temporal do grid (PASA v65.0)

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
                # Backoff exponencial com jitter
                wait = (2 ** retry_count) + random.uniform(2, 5)
                await asyncio.sleep(wait)

        return {
            "comments": all_comments,
            "post_metas": []
        }

    async def _validate_target_identity(self, page: Page, expected_username: str) -> Dict[str, Any]:
        """Verifica se a página carregada condiz com o alvo esperado via Bio e Nome (v64.0)."""
        
        # 1. Verifica página inexistente
        page_content = await page.content()
        error_indicators = ["Esta página não está disponível", "Page Not Found", "Sorry, this page"]
        if any(ind in page_content for ind in error_indicators):
            return {"valid": False, "reason": "404_not_found"}

        # 2. Captura Metadados Biográficos para Validação de IA
        bio_info = await page.evaluate("""
            () => {
                const header = document.querySelector('header');
                if (!header) return null;
                const name = header.querySelector('h1') ? header.querySelector('h1').innerText : '';
                const bio = header.querySelector('section div:last-child span') ? header.querySelector('section div:last-child span').innerText : '';
                
                // Captura seguidores (ex: "8,1 mi seguidores")
                const stats = Array.from(header.querySelectorAll('ul li'));
                const followersEl = stats.find(s => s.innerText.includes('seguidor') || s.innerText.includes('follower'));
                const followers = followersEl ? followersEl.innerText : '0';
                
                // Captura selo de verificado
                const is_verified = !!header.querySelector('svg[aria-label*="Verified"], svg[aria-label*="Verificado"]');
                
                return { name, bio, followers, is_verified };
            }
        """)

        # 3. Verifica se a conta é privada
        is_private = await page.query_selector("text='Esta conta é privada'")
        if is_private:
            return {"valid": False, "reason": "account_private"}

        # 4. Retorna dados para o worker decidir se chama a IA de validação
        return {
            "valid": True, 
            "reason": "ok",
            "biography": bio_info.get("bio", "") if bio_info else "",
            "display_name": bio_info.get("name", "") if bio_info else "",
            "followers": bio_info.get("followers", "0") if bio_info else "0",
            "is_verified": bio_info.get("is_verified", False) if bio_info else False
        }

    async def open_post_modal(self, page: Page, shortcode: str) -> bool:
        """Abre um post do Instagram via navegação direta por URL (PASA v84.3).
        
        Estratégia principal: navegação direta a /p/{shortcode}/ — mais confiável
        que o clique no grid, que sofre de timeout ao não encontrar o elemento.
        Fallback: clique no elemento do grid se já estivermos na página do perfil.
        """
        if page.is_closed():
            logger.warning("⚠️ [V2] Não é possível abrir o modal: a página está fechada.")
            return False
        
        # Estratégia 1: Navegação direta por URL (primária — sem dependência de DOM do grid)
        try:
            post_url = f"https://www.instagram.com/p/{shortcode}/"
            await page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))
            if page.is_closed():
                return False
            # Verifica se a página do post foi carregada (artigo presente)
            article = await page.query_selector("article")
            if article:
                logger.debug(f"✅ [V2] Post {shortcode} aberto via navegação direta.")
                return True
            logger.warning(f"⚠️ [V2] Post {shortcode} carregado via URL mas sem artigo detectado.")
            return True  # Continua mesmo assim, os dados JSON já foram interceptados
        except Exception as e:
            logger.warning(f"⚠️ [V2] Navegação direta para {shortcode} falhou: {e}. Tentando clique no grid...")
        
        # Estratégia 2: Clique no elemento do grid (fallback)
        selector = f'a[href*="/{shortcode}/"]'
        try:
            post_element = await page.query_selector(selector)
            if not post_element:
                logger.warning(f"⚠️ [V2] Elemento do post {shortcode} não encontrado no feed para clique.")
                return False
            await post_element.click(timeout=10000)
            await asyncio.sleep(random.uniform(3, 5))
            return True
        except Exception as e:
            logger.warning(f"⚠️ [V2] Falha ao abrir modal do post {shortcode} via clique: {e}")
            return False

    async def scroll_comment_column(self, page: Page, scroll_amount: int = 800) -> None:
        """Move o mouse e rotaciona a roda para carregar os comentários no modal."""
        await page.mouse.move(1000, 400)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(3)

    async def close_post_modal(self, page: Page) -> None:
        """Fecha a página do post retornando ao perfil do candidato (PASA v84.3).
        
        Como agora usamos navegação direta em vez de modal, o 'fechamento' é
        simplesmente voltar na history do navegador com page.go_back().
        """
        if page.is_closed():
            return
        try:
            await page.go_back(wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(random.uniform(2, 3))
        except Exception as e:
            logger.warning(f"⚠️ [V2] Falha ao voltar para o perfil após visitar o post: {e}")
            # Fallback: tecla Escape
            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)
            except Exception:
                pass

    async def _scrape_post(self, page: Page, shortcode: str, username: str, candidato_id: str, max_comments: int, max_age_days: int) -> List[Dict[str, Any]]:
        """Extrai comentários de um post específico com verificação de data e duplicidade."""
        self.captured_data = []
        
        try:
            if page.is_closed():
                return []
                
            # 1. Abre o modal
            opened = await self.open_post_modal(page, shortcode)
            if not opened:
                return []

            # 2. Verificação de Idade (Time-To-Live do Post)
            post_date_iso = await page.evaluate("""
                () => {
                    const timeEl = document.querySelector('article time');
                    return timeEl ? timeEl.getAttribute('datetime') : null;
                }
            """)
            
            if post_date_iso:
                post_dt = datetime.fromisoformat(post_date_iso.replace('Z', '+00:00'))
                age_days = (datetime.now(timezone.utc) - post_dt).days
                if age_days > max_age_days:
                    logger.info(f"⏳ [V2] Post {shortcode} ignorado por idade ({age_days} dias). Teto: {max_age_days}d")
                    await self.close_post_modal(page)
                    return []

            # 3. Rola a coluna de comentários
            for _ in range(3):
                await self.scroll_comment_column(page, scroll_amount=1200)
                await asyncio.sleep(1.5)
            
            # 4. Tenta extrair dados (Tiers de Resiliência)
            comments = self._parse_captured_json(shortcode)
            if not comments:
                comments = await self._extract_from_scripts(page, shortcode)
            if not comments:
                self.stats["browser_renders"] += 1
                comments = await self._extract_from_dom(page, shortcode)

            # 📸 EVIDÊNCIA VISUAL DE VAZIO (PASA v70.4)
            if not comments:
                await self._take_screenshot(page, f"vazio_{username}_{shortcode}")

            # 5. Fecha o modal
            await self.close_post_modal(page)
            
            # Normalização final
            now = datetime.now(timezone.utc).isoformat()
            normalized = []
            
            junk_patterns = ['também da meta', 'instagram lite', 'localizações', 'campanha 2201', 'áudio original']
            
            for c in comments[:max_comments]:
                texto = c.get("texto_bruto") or c.get("texto", "")
                
                # 🧼 DATA SCRUBBING (v57.0): Limpeza profunda para banco de dados
                # Remove caracteres nulos, formata emojis e limita tamanho
                texto = texto.replace("\u0000", "").replace("\x00", "").strip()
                if len(texto) > 2000: texto = texto[:1997] + "..."
                
                lower_text = texto.lower()
                
                # Heurística de Lixo Local
                is_junk = False
                if len(lower_text) < 2:
                    is_junk = True
                elif any(p in lower_text for p in junk_patterns):
                    is_junk = True
                elif lower_text.startswith("seguido(a) por"):
                    is_junk = True
                elif re.match(r"^[\w\s]+ \([\w\s]+\)$", texto):
                    is_junk = True
                    
                if is_junk:
                    self.stats["junk_detected"] += 1
                    continue
                    
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
            
            self.stats["comments_extracted"] += len(normalized)
            return normalized

        except Exception as e:
            logger.error(f"⚠️ [V2] Falha ao processar post {shortcode} via modal: {e}")
            if not page.is_closed():
                await self._take_screenshot(page, f"error_{username}_{shortcode}")
                try: await self.close_post_modal(page)
                except: pass
            return []

    async def _extract_shortcodes(self, page: Page, limit: int) -> List[Dict[str, Any]]:
        """Extrai shortcodes e identifica se estão fixados (pinned)."""
        return await page.evaluate(f"""
            () => {{
                const results = [];
                // Seletor para os itens do grid de postagens
                const posts = document.querySelectorAll('div._aabd, div._ac7v div');
                
                posts.forEach(p => {{
                    const link = p.querySelector('a[href*="/p/"], a[href*="/reel/"]');
                    if (!link) return;
                    
                    const href = link.href;
                    const match = href.match(/\\/(p|reel)\\/([^/]+)\\//);
                    if (!match) return;
                    
                    const shortcode = match[2];
                    if (results.some(r => r.shortcode === shortcode)) return;

                    // Detecta ícone de pin (fixado)
                    const hasPinIcon = !!p.querySelector('svg[aria-label*="Pinned"], svg[aria-label*="Fixado"], svg[aria-label*="fixada"]');

                    // Tenta capturar o timestamp (às vezes disponível no 'time' do grid ou title do link)
                    const timeEl = p.querySelector('time');
                    const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

                    results.push({{ 
                        shortcode, 
                        is_pinned: hasPinIcon,
                        timestamp: timestamp 
                    }});
                    }});

                return results.slice(0, {limit + 3});
            }}
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
            except:
                continue
        return comments

    async def _extract_from_dom(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        """Heurística estruturada baseada em blocos de comentários (PASA v52.6)."""
        return await page.evaluate("""
            () => {
                const results = [];
                const container = document.querySelector('article') || document;
                // Comentaristas geralmente ficam em h3 na estrutura atual do modal
                const h3s = Array.from(container.querySelectorAll('h3'));
                
                const commentTextBlacklist = [
                    'ver respostas', 'ocultar respostas', 'ver tradução', 'ver traduções',
                    'ver resposta', 'ocultar resposta', 'reply', 'view replies', 'hide replies',
                    'view translation', 'curtir', 'like', 'responder', 'reply',
                    'enviar', 'send', 'compartilhar', 'share', 'carregar mais comentários',
                    'carregar mais', 'load more comments', 'load more',
                    'áudio original', 'original audio', 'som original', 'original sound',
                    'adicionar um comentário...', 'add a comment...', 'curtido por', 'liked by',
                    'também da meta', 'instagram lite', 'localizações', 'campanha 2201'
                ];
                
                h3s.forEach(h => {
                    const username = h.innerText.trim();
                    // Validação básica do username para evitar lixo
                    if (!username || username.includes(' ') || username.length < 2) return;
                    
                    let node = h;
                    // Sobe na árvore do DOM para englobar todo o bloco do comentário (geralmente 5-6 níveis)
                    for(let i = 0; i < 6; i++) { if(node.parentElement) node = node.parentElement; }
                    
                    // Procura o texto do comentário dentro desse bloco
                    const spans = Array.from(node.querySelectorAll('span[dir="auto"], div[dir="auto"]'));
                    let commentText = null;
                    
                    for(let span of spans) {
                        const txt = span.innerText.trim();
                        if (!txt || txt === username) continue;
                        
                        const lowerTxt = txt.toLowerCase();
                        // Ignora timestamps e termos de blacklist estrita
                        const isTime = /^[0-9]+[ ]?(h|d|m|w|y|sem|a|s)$/i.test(txt) || /^[0-9]+[ ]?(horas|dias|semanas|anos|segundos|minutos)/i.test(txt);
                        const isBlacklist = commentTextBlacklist.some(b => lowerTxt === b || lowerTxt.startsWith(b));
                        
                        // Ignora comentários compostos APENAS por emojis ou pontuação (sem nenhuma letra ou número)
                        const hasLetters = /[\\p{L}\\p{N}]/u.test(txt);
                        
                        if (!isTime && !isBlacklist && hasLetters) {
                            commentText = txt;
                            break;
                        }
                    }
                    
                    if(commentText) {
                        results.push({ autor: username, texto: commentText });
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

    async def _verify_session(self, page: Page, session: Session) -> bool:
        """Verifica se a sessão está funcional na Home do Instagram (PASA v83.2)."""
        try:
            # Navega para a Home para validar cookies injetados de forma estável
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)
            
            current_url = page.url
            if "accounts/login" in current_url:
                return False
                
            # Verifica a visibilidade de campos de login
            login_field = await page.query_selector('input[name="username"], input[name="password"]')
            if login_field and await login_field.is_visible():
                return False
                
            return True
        except Exception as e:
            logger.warning(f"⚠️ [V2] Erro na verificação de sessão: {e}")
            return False

    async def _take_screenshot(self, page: Page, name: str) -> None:
        """Captura evidência visual da falha para auditoria (PASA v70.4)."""
        try:
            if page.is_closed():
                logger.warning(f"⚠️ Não é possível tirar screenshot: a página está fechada.")
                return
            folder = os.path.join("logs", "evidence")
            os.makedirs(folder, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(folder, f"{ts}_{name}.png")
            await page.screenshot(path=path, full_page=True, timeout=5000)
            logger.info(f"📸 Evidência visual salva: {path}")
        except Exception as e:
            logger.error(f"❌ Falha ao capturar screenshot: {e}")

async def scrape_instagram(username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50) -> List[Dict[str, Any]]:
    """Função utilitária rápida."""
    scraper = InstagramScraperV2()
    return await scraper.scrape_profile(username, candidato_id, max_posts, max_comments_per_post)
