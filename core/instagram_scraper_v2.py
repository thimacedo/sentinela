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

                    # Check imediato de erro 404 antes do sleep longo
                    try:
                        error_header = await page.query_selector("h2")
                        if error_header:
                            header_text = await error_header.inner_text()
                            if "Página não disponível" in header_text or "Sorry, this page" in header_text:
                                logger.error(f"❌ [V2] Alvo @{username} inexistente (404 detectado no H2).")
                                await browser.close()
                                raise ValueError(f"invalid_target: 404_not_found")
                    except ValueError as ve: raise ve
                    except: pass

                    await asyncio.sleep(random.uniform(5, 10))

                    if "login" in page.url:
                        logger.warning(f"⚠️ [V2] Login wall detectado para {session.label}")
                        session.blocked = True
                        self.stats["session_rotations"] += 1
                        retry_count += 1
                        await browser.close()
                        continue

                    # 🛡️ VALIDAÇÃO BIOGRÁFICA (v64.0): IA verifica se a Bio condiz com o alvo
                    validation = await self._validate_target_identity(page, username)
                    if not validation["valid"]:
                        logger.error(f"❌ [V2] Alvo @{username} inválido: {validation['reason']}")
                        await browser.close()
                        raise ValueError(f"invalid_target: {validation['reason']}")
                    
                    # Chamada de IA para validar identidade
                    bio_check = await ai_service.validate_identity(
                        expected_name=candidato_id, # Usamos o candidato_id (que deve conter o nome/contexto do alvo)
                        display_name=validation.get("display_name", ""),
                        bio=validation.get("biography", "")
                    )

                    if not bio_check.get("is_authentic", True):
                        logger.error(f"🚫 [V2] ALVO INAUTÊNTICO DETECTADO: @{username}. Motivo: {bio_check.get('reason')}")
                        await browser.close()
                        raise ValueError(f"inauthentic_identity: {bio_check.get('reason')}")

                    # Extrai metadados dos posts (shortcode + is_pinned)
                    post_metas = await self._extract_shortcodes(page, max_posts)
                    self.stats["posts_found"] = len(post_metas)
                    
                    scraped_count = 0
                    for meta in post_metas:
                        if scraped_count >= max_posts:
                            break
                            
                        shortcode = meta["shortcode"]
                        is_pinned = meta["is_pinned"]
                        post_timestamp = meta.get("timestamp")
                        
                        # 1. Skip de Fixados (v62.0)
                        if is_pinned:
                            logger.info(f"⏭️ [V2] Post {shortcode} FAST-SKIP (Fixado).")
                            continue

                        # 2. Fast-Skip Temporal (v62.1): Verifica data diretamente do grid se disponível
                        if post_timestamp:
                            try:
                                post_dt = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00'))
                                age_days = (datetime.now(timezone.utc) - post_dt).days
                                if age_days > max_age_days:
                                    logger.info(f"⏭️ [V2] Post {shortcode} FAST-SKIP (Velho: {age_days}d). Encerrando busca neste perfil.")
                                    # Se chegamos em posts velhos no grid (e não é pin), o resto também será velho.
                                    break 
                            except: pass

                        logger.info(f"📄 [V2] Analisando post {shortcode} (Novo/Recente)")
                        
                        # Processa o post
                        post_comments = await self._scrape_post(page, shortcode, username, candidato_id, max_comments_per_post, max_age_days)
                        
                        if post_comments:
                            all_comments.extend(post_comments)
                            scraped_count += 1
                            self.stats["posts_scraped"] += 1
                            # Jitter agressivo entre posts
                            await asyncio.sleep(random.uniform(5, 15))
                        else:
                            logger.info(f"⏭️ [V2] Post {shortcode} ignorado (velho, fixado já visto ou sem comentários).")

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
                return { name, bio };
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
            "display_name": bio_info.get("name", "") if bio_info else ""
        }

    async def open_post_modal(self, page: Page, shortcode: str) -> bool:
        """Encontra e clica na postagem no feed do perfil para abrir o modal."""
        selector = f'a[href*="/{shortcode}/"]'
        post_element = await page.query_selector(selector)
        if not post_element:
            logger.warning(f"⚠️ [V2] Elemento do post {shortcode} não encontrado no feed.")
            return False
            
        await post_element.click()
        # Aguarda abertura e requisições iniciais
        await asyncio.sleep(random.uniform(5, 7))
        return True

    async def scroll_comment_column(self, page: Page, scroll_amount: int = 800) -> None:
        """Move o mouse e rotaciona a roda para carregar os comentários no modal."""
        await page.mouse.move(1000, 400)
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(3)

    async def close_post_modal(self, page: Page) -> None:
        """Fecha o modal de postagem simulando a tecla Escape."""
        await page.keyboard.press("Escape")
        await asyncio.sleep(random.uniform(2, 3))

    async def _scrape_post(self, page: Page, shortcode: str, username: str, candidato_id: str, max_comments: int, max_age_days: int) -> List[Dict[str, Any]]:
        """Extrai comentários de um post específico com verificação de data e duplicidade."""
        self.captured_data = []
        
        try:
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

async def scrape_instagram(username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50) -> List[Dict[str, Any]]:
    """Função utilitária rápida."""
    scraper = InstagramScraperV2()
    return await scraper.scrape_profile(username, candidato_id, max_posts, max_comments_per_post)
