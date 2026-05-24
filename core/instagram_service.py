from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from playwright.async_api import Page, BrowserContext, async_playwright

logger = logging.getLogger("instagram_service")

class InstagramService:
    """
    Serviço centralizado para raspagem do Instagram seguindo os 4 Tiers de Resiliência.
    PASA v51.0
    """

    def __init__(self, storage_state_path: str = "configs/instagram_storage_state.json"):
        self.storage_state_path = storage_state_path
        self.captured_data: List[Dict[str, Any]] = []

    async def _handle_response(self, response):
        """Interceptador de rede para capturar JSONs de interesse."""
        url = response.url
        if "graphql" in url or "comments" in url:
            try:
                # Evita carregar corpo de respostas gigantes irrelevantes (ex: imagens)
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.captured_data.append({"url": url, "data": data})
            except Exception:
                pass

    async def scrape_candidate_comments(self, page: Page, username: str, max_posts: int = 3) -> List[Dict[str, Any]]:
        """
        Coleta comentários de um candidato navegando pelo seu perfil.
        Implementa Tiers de Resiliência progressivos.
        """
        self.captured_data = []
        all_comments = []

        logger.info(f"🎯 [IGService] Iniciando coleta para @{username} (limite {max_posts} posts)")

        # Registra listener
        page.on("response", self._handle_response)

        try:
            # 1. Acessa perfil
            await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5) # Espera renderização inicial

            # 2. Coleta shortcodes dos posts
            shortcodes = await self._extract_shortcodes(page, max_posts)
            if not shortcodes:
                logger.warning(f"⚠️ [IGService] Nenhum post encontrado para @{username}")
                return []

            logger.info(f"📦 [IGService] Encontrados {len(shortcodes)} posts para processar.")

            for code in shortcodes:
                post_url = f"https://www.instagram.com/p/{code}/"
                logger.info(f"📄 [IGService] Processando post: {post_url}")
                
                # Reseta capturas para este post específico
                self.captured_data = []
                
                await page.goto(post_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                
                # Rola para carregar comentários (Comet exige isso)
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(5)

                # Tier 2: Network Interception (Captura JSON do Comet/Relay)
                comments = self._parse_network_captures(code)
                tier = "Tier 2 (Network)"
                
                # Tier 3: Script Extractions (Preloaders data-sjs)
                if not comments:
                    comments = await self._extract_from_scripts(page, code)
                    tier = "Tier 3 (Scripts)"

                # Tier 4: DOM Selectors (Último recurso)
                if not comments:
                    comments = await self._extract_from_dom(page, code)
                    tier = "Tier 4 (DOM)"

                if comments:
                    logger.info(f"✅ [IGService] {len(comments)} comentários extraídos via {tier} para {code}")
                    # Normaliza dados para o esquema Sentinela
                    for c in comments:
                        c["candidato_id"] = username
                        c["post_shortcode"] = code
                        c["plataforma"] = "INSTAGRAM"
                        c["rede_social"] = "INSTAGRAM"
                        c["data_coleta"] = datetime.now(timezone.utc).isoformat()
                        c["processado_ia"] = False
                        c["mined"] = True
                        # Garante campos obrigatorios
                        if "texto_bruto" not in c: c["texto_bruto"] = c.get("texto", "")
                        if "autor_username" not in c: c["autor_username"] = c.get("autor", "unknown")
                        if "data_publicacao" not in c: c["data_publicacao"] = c.get("timestamp", c["data_coleta"])
                    all_comments.extend(comments)
                else:
                    logger.warning(f"❌ [IGService] Falha total na extração para {code}")

        except Exception as e:
            logger.error(f"💥 [IGService] Erro crítico na coleta de @{username}: {e}", exc_info=True)
        finally:
            page.remove_listener("response", self._handle_response)

        return all_comments

    async def _extract_shortcodes(self, page: Page, limit: int) -> List[str]:
        """Extrai shortcodes do perfil via DOM (Robusto)."""
        return await page.evaluate(f"""
            () => Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"], a[href*="/reels/"]'))
                .map(a => {{
                    const match = a.href.match(/\\/(p|reel|reels)\\/([^/]+)\\//);
                    return match ? match[2] : null;
                }})
                .filter(Boolean)
                .slice(0, {limit})
        """)

    def _parse_network_captures(self, shortcode: str) -> List[Dict[str, Any]]:
        """Processa os JSONs capturados da rede procurando por comentários."""
        comments = []
        for item in self.captured_data:
            data = item["data"]
            data_str = json.dumps(data)
            
            # Padrão Novo (Comet/xdt)
            if "xdt_api__v1__media" in data_str:
                # TODO: Implementar parser profundo para xdt_
                pass
            
            # Padrão Clássico (edge_media_to_parent_comment)
            if "edge_media_to_parent_comment" in data_str:
                # Tenta localizar o nó de mídia
                # Pode estar em data.shortcode_media ou em outros lugares dependendo da query
                try:
                    # Busca recursiva simples por texto e autor
                    # Para simplificar agora, vamos apenas extrair o que parece comentário
                    extracted = self._recursive_find_comments(data)
                    if extracted:
                        comments.extend(extracted)
                except Exception:
                    pass
        
        return self._deduplicate_comments(comments)

    async def _extract_from_scripts(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        """Extrai comentários de scripts JSON (data-sjs) injetados na página."""
        script_contents = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script[type="application/json"]'))
                .map(s => s.innerText)
                .filter(txt => txt.includes('xdt_api__v1__media') || txt.includes('edge_media_to_parent_comment'))
        """)
        
        comments = []
        for content in script_contents:
            try:
                data = json.loads(content)
                extracted = self._recursive_find_comments(data)
                if extracted:
                    comments.extend(extracted)
            except Exception:
                continue
        
        return self._deduplicate_comments(comments)

    async def _extract_from_dom(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        """Fallback agressivo via DOM: captura spans e tenta associar autor/texto."""
        
        raw_data = await page.evaluate("""
            () => {
                const results = [];
                const spans = Array.from(document.querySelectorAll('span[dir="auto"]'));
                
                const blacklist = ['explorar', 'explore', 'mensagens', 'messages', 'notificações', 'notifications', 
                                 'criar', 'create', 'painel', 'dashboard', 'perfil', 'profile', 'mais', 'more',
                                 'responder', 'reply', 'ver todas as', 'view all', 'pesquisa', 'search',
                                 'reels', 'home', 'página inicial', 'direct', 'threads', 'configurações', 'settings'];

                let lastUsername = "";
                for (let i = 0; i < spans.length; i++) {
                    const txt = spans[i].innerText.trim();
                    if (txt.length === 0) continue;
                    
                    const isUsername = /^[a-z0-9._]{3,30}$/i.test(txt) && !txt.includes(' ') && !blacklist.includes(txt.toLowerCase());
                    
                    if (isUsername) {
                        lastUsername = txt;
                    } else if (txt.length > 1 && lastUsername) {
                        // Ignora timestamps (ex: 1 h, 2 d, 35 m)
                        if (/^[0-9]+[ ]?[hdm]$/i.test(txt)) continue;
                        // Ignora "Like" e "Reply"
                        if (blacklist.some(b => txt.toLowerCase().includes(b))) continue;
                        
                        results.push({ username: lastUsername, text: txt });
                        lastUsername = ""; 
                    }
                }
                return results;
            }
        """)
        
        comments = []
        for item in raw_data:
            # Ignora textos que parecem ser metadados (Reply, likes, etc)
            if item["text"].lower() in ["reply", "responder", "view replies", "see translation"]:
                continue
            if "like" in item["text"].lower() and len(item["text"]) < 10:
                continue
                
            comments.append({
                "texto_bruto": item["text"],
                "autor_username": item["username"],
                "data_publicacao": datetime.now(timezone.utc).isoformat(),
                "id_externo": f"dom_{shortcode}_{hash(item['text'] + item['username'])}"
            })
        
        return self._deduplicate_comments(comments)

    def _recursive_find_comments(self, data: Any) -> List[Dict[str, Any]]:
        """Busca recursiva por padrões de comentários em objetos JSON complexos."""
        comments = []
        
        if isinstance(data, dict):
            # Padrão edge_media_to_parent_comment
            if "edge_media_to_parent_comment" in data:
                edges = data["edge_media_to_parent_comment"].get("edges", [])
                for edge in edges:
                    node = edge.get("node", {})
                    comments.append({
                        "texto": node.get("text", ""),
                        "autor": node.get("owner", {}).get("username", "unknown"),
                        "timestamp": datetime.fromtimestamp(node.get("created_at", 0), timezone.utc).isoformat(),
                        "id_externo": node.get("id", "")
                    })
            
            # Padrão xdt_ (Comet)
            elif "xdt_api__v1__media__shortcode__web_info" in data:
                items = data["xdt_api__v1__media__shortcode__web_info"].get("items", [])
                for item in items:
                    # O Comet às vezes traz preview_comments ou exige outra query
                    # Se houver preview_comments aqui, pegamos
                    preview = item.get("preview_comments", [])
                    for c in preview:
                        comments.append({
                            "texto": c.get("text", ""),
                            "autor": c.get("user", {}).get("username", "unknown"),
                            "timestamp": datetime.fromtimestamp(c.get("created_at", 0), timezone.utc).isoformat(),
                            "id_externo": c.get("pk", "")
                        })
            
            # Continua busca recursiva
            for v in data.values():
                comments.extend(self._recursive_find_comments(v))
                
        elif isinstance(data, list):
            for item in data:
                comments.extend(self._recursive_find_comments(item))
                
        return comments

    def _deduplicate_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicados da lista de comentários baseados no texto ou id_externo."""
        seen_ids = set()
        unique = []
        for c in comments:
            cid = c.get("id_externo") or c.get("texto")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                unique.append(c)
        return unique
