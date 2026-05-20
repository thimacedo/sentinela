import asyncio
import json
import logging
import os
import sys
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from core.supabase_service import supabase as db

logger = logging.getLogger("InstagramWorker")

# --- Imports Resilientes ---
ScraperZyte = None
ScraperHeadless = None
ZYTE_AVAILABLE = False
HEADLESS_AVAILABLE = False

try:
    from scraper_zyte import InstagramScraperZyte as ScraperZyte
    ZYTE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Motor Zyte indisponível: {e}")

try:
    from scraper_headless import InstagramScraperHeadless as ScraperHeadless
    HEADLESS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Motor Playwright indisponível: {e}")


class InstagramWorker:
    """
    Orquestrador de Tiers para coleta do Instagram.
    Tier 1: API GraphQL (Scrapy)
    Tier 2: DOM Rendering (Scrapy + Playwright)
    Tier 3: Zyte Cloud
    Tier 4: Playwright Solo (Fallback local)
    """
    
    def __init__(self):
        self.engine_type = "none"
        if ZYTE_AVAILABLE:
            self.engine_type = "zyte"
        elif HEADLESS_AVAILABLE:
            self.engine_type = "playwright"

    def _get_active_session(self) -> Optional[Dict[str, Any]]:
        """Busca uma sessão ativa (cookies) no Supabase."""
        try:
            res = (
                db.table("worker_sessions")
                .select("id, cookies")
                .eq("plataforma", "instagram")
                .eq("status", "active")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Erro ao buscar sessão ativa: {e}")
        return None

    def _extract_sessionid(self, cookies: Any) -> str:
        """Extrai sessionid de diferentes formatos de cookie."""
        if isinstance(cookies, str):
            for part in cookies.split(";"):
                if "sessionid=" in part.strip():
                    return part.split("=")[1].strip()
        elif isinstance(cookies, list):
            for c in cookies:
                if c.get("name") == "sessionid":
                    return c.get("value", "")
        return ""

    async def _rotate_session(self, bad_session_id: str) -> Optional[Dict[str, Any]]:
        """Marca a sessão atual como falha e busca uma nova no Supabase."""
        if not bad_session_id:
            return None
            
        logger.warning(f"🔄 Rotacionando sessão. Marcando {bad_session_id} como expirada...")
        try:
            db.table("worker_sessions").update({"status": "expired"}).eq("id", bad_session_id).execute()
        except Exception:
            pass
            
        new_session = self._get_active_session()
        if new_session and new_session.get("id") != bad_session_id:
            logger.info(f"✅ Nova sessão obtida: {new_session['id']}")
            return new_session
            
        logger.error("❌ Nenhuma sessão alternativa disponível para rotação.")
        return None

    def run(self, target: str) -> bool:
        """Ponto de entrada síncrono chamado pelo local_server.py"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._run_async(target))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"💥 ERRO CRÍTICO: {e}")
            return False

    async def _run_scrapy_tier(self, spider_name: str, target: str, session_id: str, max_posts: int) -> List[Dict]:
        """Executa um spider do Scrapy em processo isolado."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as tmp:
            output_path = tmp.name
        
        try:
            python_exe = sys.executable
            # Caminho absoluto para o runner
            script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'scripts', 'run_scrapy_spider.py')
            
            cmd = [
                python_exe, script_path,
                spider_name, target, session_id, str(max_posts), output_path
            ]
            
            tier_num = 1 if 'api' in spider_name else 2
            logger.info(f"🕷️ Tier {tier_num}: Executando {spider_name} para @{target}")
            
            timeout = 90 if spider_name == 'instagram_api' else 240
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            logger.info(f"⏳ Tier {tier_num}: Processando @{target}... (aguardando Scrapy)")
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"❌ Tier {tier_num} ({spider_name}) FALHOU (Code {process.returncode})")
                if error_msg:
                    # Loga apenas as últimas 3 linhas do erro para não poluir
                    last_lines = "\n".join(error_msg.strip().split("\n")[-3:])
                    logger.error(f"Destaque do erro:\n{last_lines}")
                return []
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                with open(output_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data:
                    logger.info(f"✅ Tier {tier_num}: Scrapy extraiu {len(data)} comentários com sucesso.")
                    return data
            
            logger.warning(f"⚠️ Tier {tier_num}: Scrapy terminou sem extrair dados.")
            return []
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Tier {tier_num} ({spider_name}): Timeout excedido")
            return []
        except Exception as e:
            logger.error(f"❌ Tier {tier_num} ({spider_name}): Erro: {e}")
            return []
        finally:
            if os.path.exists(output_path):
                try: os.unlink(output_path)
                except: pass

    async def _run_async(self, target: str) -> bool:
        """Orquestrador principal com cascata de Tiers."""
        from core.state_manager import WorkerState
        
        worker_state = WorkerState("instagram_worker")
        current_level = worker_state.level
        trust = worker_state.trust_score
        
        known_shortcodes = worker_state.get(f"{target}_shortcodes", [])
        logger.info(f"🧬 Worker Nível {current_level} | Trust: {trust:.1f} | Alvo: @{target} | Conhecidos: {len(known_shortcodes)}")
        
        session = self._get_active_session()
        cookies = session.get("cookies") if session else None
        session_id = self._extract_sessionid(cookies)
        
        scraped_data = []
        tier_used = 0

        # --- TIER 1: Scrapy API ---
        if session_id:
            scraped_data = await self._run_scrapy_tier('instagram_api', target, session_id, max_posts=5)
            if scraped_data:
                tier_used = 1
                logger.info(f"✅ Tier 1 bem-sucedido: {len(scraped_data)} itens")

        # --- TIER 2: Scrapy DOM (Fallback se Tier 1 falhou) ---
        if not scraped_data and session_id:
            logger.warning("⚠️ Tier 1 falhou. Tentando Tier 2: DOM Rendering...")
            scraped_data = await self._run_scrapy_tier('instagram_dom', target, session_id, max_posts=3)
            if scraped_data:
                tier_used = 2
                logger.info(f"✅ Tier 2 bem-sucedido: {len(scraped_data)} itens")

        # --- TIER 3: Zyte Cloud (Fallback Premium) ---
        if not scraped_data:
            zyte_disabled = os.getenv("ZYTE_DISABLED", "false") == "true"
            if not zyte_disabled and ZYTE_AVAILABLE:
                logger.warning("⚠️ Scrapy Tiers falharam. Tentando Tier 3: Zyte Cloud...")
                try:
                    zyte = ScraperZyte(target, max_posts=5)
                    posts = await zyte.fetch_recent_posts(external_cookies=cookies, skip_shortcodes=known_shortcodes)
                    # Converte posts do Zyte para o formato de comentários se necessário
                    # No sistema atual, save_posts aceita o formato de posts do Zyte
                    if posts and not all(p.get("is_skipped") for p in posts):
                        await self._save_posts(target, posts)
                        worker_state.record_success(items_saved=len(posts))
                        # Atualiza memória
                        all_sc = list(set(known_shortcodes + [p.get("shortcode") for p in posts if p.get("shortcode")]))
                        worker_state.save({f"{target}_shortcodes": all_sc[-20:]})
                        return True
                except Exception as e:
                    logger.error(f"❌ Tier 3 (Zyte) falhou: {e}")

        # --- TIER 4: Playwright Solo (Último recurso) ---
        if not scraped_data and HEADLESS_AVAILABLE:
             logger.warning("⚠️ Todos os tiers falharam. Tentando Tier 4: Playwright Solo...")
             try:
                 headless = ScraperHeadless(target, max_posts=5, max_comments=20)
                 posts = await headless.fetch_recent_posts(external_cookies=cookies)
                 if posts:
                     await self._save_posts(target, posts)
                     worker_state.record_success(items_saved=len(posts))
                     return True
             except Exception as e:
                 logger.error(f"❌ Tier 4 falhou: {e}")

        # Se chegamos aqui com dados dos Tiers 1 ou 2 (Scrapy)
        if scraped_data:
            # Formata dados do Scrapy para o save_posts (que espera Posts com lista de comentários)
            # Como o Scrapy retorna uma lista flat de comentários:
            fake_post = {"shortcode": f"tier{tier_used}_bulk", "comments": scraped_data}
            await self._save_posts(target, [fake_post])
            worker_state.record_success(items_saved=len(scraped_data))
            return True

        worker_state.record_failure(reason="all_tiers_failed")
        return False

    async def _save_posts(self, target: str, posts: List[Dict]) -> None:
        """Salva posts e comentários no Supabase com Quality Gate e Retry."""
        try:
            from app.workers.quality_gate import filter_comment
        except ImportError:
            filter_comment = lambda text: len(text.strip()) >= 3

        total_saved = 0
        for post in posts:
            comments = post.get("comments", [])
            for comment in comments:
                text = comment.get("text", "")
                if not filter_comment(text): continue

                comment_row = {
                    "candidato_id": target,
                    "texto_bruto": text.strip(),
                    "autor_username": comment.get("ownerUsername", "unknown"),
                    "post_shortcode": post.get("shortcode", ""),
                    "data_coleta": datetime.now(timezone.utc).isoformat(),
                    "processado_ia": False,
                    "is_hate": False,
                }
                
                for attempt in range(3):
                    try:
                        db.table("comentarios").insert(comment_row).execute()
                        total_saved += 1
                        break
                    except Exception as e:
                        if attempt < 2: await asyncio.sleep(2 * (attempt + 1))
                        else: logger.error(f"❌ Erro ao salvar comentário: {e}")

        if total_saved > 0:
            logger.info(f"💾 {total_saved} salvos para @{target}")
            try:
                db.table("candidatos").update({
                    "last_scraped_at": datetime.now(timezone.utc).isoformat(),
                }).eq("username", target).execute()
            except: pass
