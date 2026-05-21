from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service
from core.circuit_breaker import zyte_circuit_breaker
import logging
import os
import json
import asyncio
import base64
import httpx
import re
from datetime import datetime, timezone

@dataclass
class Target:
    username: str
    candidato_id: Optional[str] = None
    queue_id: Optional[str] = None
    source: str = "unknown"

@dataclass
class PersistStats:
    inserted: int = 0
    duplicated: int = 0
    failed: int = 0
    inserted_ids: list[str] = field(default_factory=list)
    success: bool = False

@dataclass
class ClassifyStats:
    classified: int = 0
    failed: int = 0
    success: bool = False

class IGZyteWorker(BaseWorker):
    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.logger = logging.getLogger(f"worker.{worker_id}")
        self.cycle = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids = set()
        self.seen_targets = set()
        
        # Configurações Zyte
        self.zyte_key = os.getenv("ZYTE_API_KEY")
        self.zyte_api_url = "https://api.zyte.com/v1/extract"
        self.app_id = "936619743392459" # Instagram App ID padrão
        self.max_posts = config.get("max_posts", 3)

    def describe(self) -> str:
        return "Instagram Scraper via Zyte API (Real Extraction v50.1)"

    async def setup(self) -> None:
        if not self.zyte_key:
            self.logger.error("ZYTE_API_KEY não encontrada no ambiente.")
            raise RuntimeError("zyte_api_key_missing")
        self.logger.info("Motor Zyte configurado e pronto para extração real.")

    async def teardown(self) -> None:
        self.logger.info("Motor Zyte encerrado.")

    async def _zyte_request(self, url: str, headers: Dict[str, str] = None, cookies: str = None, use_browser: bool = False) -> Dict[str, Any]:
        """Faz uma requisição via Zyte API com Circuit Breaker, retentativas e rotação de sessão."""
        if not zyte_circuit_breaker.can_execute("zyte_api"):
            return {"error": "circuit_open", "status_code": 999}

        # 🔄 Rotação de Sessão ou Cookie Full
        cookie_full = os.getenv("INSTAGRAM_COOKIE_FULL")
        current_slot = "zyte_session"
        if cookie_full:
            cookies = cookie_full
            current_slot = "full_cookie"
            self.logger.debug(f"[Zyte] Usando cookie_full=presente")
        else:
            session_keys = sorted([k for k in os.environ.keys() if k.startswith("INSTAGRAM_SESSIONID")])
            if session_keys:
                import random
                idx = random.randint(0, len(session_keys) - 1)
                session_key = session_keys[idx]
                session_id = os.getenv(session_key)
                current_slot = idx + 1
                if session_id:
                    cookies = f"sessionid={session_id}; {cookies}" if cookies else f"sessionid={session_id}"
                    self.logger.debug(f"[Zyte] Usando session_slot={current_slot}")

        payload = {"url": url}
        custom_headers = []
        if headers:
            for k, v in headers.items():
                custom_headers.append({"name": k, "value": v})
        if cookies:
            custom_headers.append({"name": "Cookie", "value": cookies})

        if use_browser:
            payload["browserHtml"] = True
            payload["javascript"] = True
        else:
            payload["httpResponseBody"] = True
            if custom_headers:
                payload["customHttpRequestHeaders"] = custom_headers

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(self.zyte_api_url, auth=(self.zyte_key, ""), json=payload)
                
                # 🛑 Backoff e Erros de Sessão
                if response.status_code in [401, 403]:
                    self.logger.warning(f"⚠️ [Zyte] Erro de autenticação (HTTP {response.status_code}) no slot={current_slot}. Sessão pode estar inválida.")
                    return {"error": "auth_failed", "status_code": response.status_code, "slot": current_slot}

                if response.status_code == 429:
                    self.logger.warning(f"⚠️ [Zyte] Rate Limited (429). Aguardando backoff...")
                    await asyncio.sleep(10 * (attempt + 1))
                    continue

                if response.status_code == 503:
                    delay = 5 * (2 ** attempt)
                    self.logger.warning(f"⚠️ [Zyte] 503 (tentativa {attempt + 1}). Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue 

                zyte_circuit_breaker.record_success("zyte_api")
                
                if response.status_code != 200:
                    self.logger.error(f"❌ Erro Zyte ({response.status_code}): {response.text[:200]}")
                    zyte_circuit_breaker.record_failure("zyte_api", response.status_code)
                    return {"error": "api_error", "status_code": response.status_code}
                
                res_data = response.json()
                
                if use_browser:
                    html = res_data.get("browserHtml", "")
                    if 'login-form' in html or 'login' in html.lower() or 'Página não disponível' in html:
                        self.logger.warning(f"🚫 [Zyte] Login Wall detectado no slot={current_slot}")
                        return {"error": "login_required", "statusCode": 401, "slot": current_slot}
                
                target_status = res_data.get("statusCode", 200)
                if target_status == 404:
                    return {"error": "not_found", "statusCode": 404}
                
                if use_browser:
                    return {"browserHtml": res_data.get("browserHtml"), "statusCode": target_status}
                
                body_b64 = res_data.get("httpResponseBody")
                if body_b64:
                    body_content = base64.b64decode(body_b64).decode('utf-8')
                    if body_content.strip().startswith('{'):
                        return json.loads(body_content)
                    return {"raw_body": body_content}
                
                return {} 

            except Exception as e:
                self.logger.error(f"🔌 [Zyte] Erro de conexão no slot={current_slot}: {e}")
                return {"error": "connection_error"}
        
        return {"error": "service_unavailable", "status_code": 503}

    def _extract_json_from_html(self, html: str) -> Dict[str, Any]:
        """Extrai o JSON do HTML do Instagram."""
        if not html: return {}
        match = re.search(r'window\.__additionalData\["xdt_api__v1__users__web_profile_info"\s*\]\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except: pass
        match = re.search(r'window\._sharedData\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except: pass
        return {}

    def _extract_from_dom(self, html: str) -> List[Dict[str, Any]]:
        """Extrai links de posts via regex se o JSON falhar."""
        if not html: return []
        posts = []
        links = re.findall(r'href="/(?:[^/]+/)?(p|reel)/([^/"]+)/"', html)
        
        seen_codes = set()
        for _, shortcode in links:
            if shortcode not in seen_codes:
                posts.append({"shortcode": shortcode})
                seen_codes.add(shortcode)
                if len(posts) >= self.max_posts:
                    break
        return posts

    async def fetch_comments_via_zyte(self, target: Target) -> list[dict]:
        """Extração real via Zyte API integrando lógica do scraper_zyte.py."""
        self.logger.info("🚀 [Zyte] Coletando perfil real: @%s", target.username)
        
        profile_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={target.username}"
        headers = {
            "X-IG-App-ID": self.app_id,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        
        # 1. Tenta via API v1 direta
        data = await self._zyte_request(profile_url, headers)
        user_data = data.get("data", {}).get("user")
        
        html = ""
        # 2. Fallback para Browser Rendering se a API falhar
        if not user_data:
            self.logger.info("🔄 [Zyte] API JSON falhou. Tentando via Browser Rendering...")
            browser_url = f"https://www.instagram.com/{target.username}/"
            browser_res = await self._zyte_request(browser_url, {"User-Agent": headers["User-Agent"]}, use_browser=True)
            
            html = browser_res.get("browserHtml", "")
            if html:
                extracted_data = self._extract_json_from_html(html)
                user_data = (extracted_data.get("data", {}).get("user") or 
                            extracted_data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user"))

        all_comments = []
        shortcodes_to_fetch = []

        if user_data:
            edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
            for edge in edges[:self.max_posts]:
                node = edge.get("node", {})
                if node.get("shortcode") and node.get("id"):
                    shortcodes_to_fetch.append({"shortcode": node["shortcode"], "media_id": node["id"]})
        elif html:
            self.logger.info("🔄 [Zyte] JSON não encontrado no HTML. Tentando extração via DOM...")
            dom_posts = self._extract_from_dom(html)
            for p in dom_posts:
                shortcodes_to_fetch.append({"shortcode": p["shortcode"], "media_id": None})

        if not shortcodes_to_fetch:
            self.logger.warning("❌ Falha ao obter posts do perfil @%s", target.username)
            return []

        for item in shortcodes_to_fetch:
            shortcode = item["shortcode"]
            media_id = item["media_id"]

            if not media_id:
                self.logger.info("⏭️ Post %s sem media_id (DOM only), pulando comentários.", shortcode)
                continue

            self.logger.info("💬 [Zyte] Coletando comentários do post %s...", shortcode)
            comments_url = f"https://www.instagram.com/api/v1/media/{media_id}/comments/"
            comments_data = await self._zyte_request(comments_url, headers)
            
            if not comments_data.get("error"):
                raw_comments = comments_data.get("comments", [])
                for c in raw_comments[:20]:
                    all_comments.append({
                        "id_externo": f"ig_{c.get('pk')}",
                        "texto_bruto": c.get("text"),
                        "autor_username": c.get("user", {}).get("username"),
                        "data_publicacao": datetime.fromtimestamp(c.get('created_at'), tz=timezone.utc).isoformat() if c.get('created_at') else datetime.now(timezone.utc).isoformat(),
                        "data_coleta": datetime.now(timezone.utc).isoformat(),
                        "post_shortcode": shortcode,
                        "plataforma": "INSTAGRAM",
                        "rede_social": "INSTAGRAM",
                        "candidato_id": target.candidato_id,
                        "processado_ia": False,
                        "mined": True
                    })
        return all_comments

    def claim_next_target(self) -> Optional[Target]:
        return self.queue.claim_next_target(self.config, self.seen_queue_ids, self.seen_targets)

    def persist_comments(self, target: Target, comments: list[dict]) -> PersistStats:
        """Persistência real no Supabase."""
        stats = PersistStats()
        if not comments:
            return stats

        sent_ids = {c["id_externo"] for c in comments if c.get("id_externo")}
        try:
            res = self.db.table('comentarios').upsert(
                comments,
                on_conflict="id_externo",
                ignore_duplicates=True
            ).execute()

            stats.inserted = len(res.data)
            stats.duplicated = len(sent_ids) - stats.inserted
            stats.inserted_ids = [str(item['id']) for item in res.data]
            stats.success = True
            self.logger.info("✅ Persistência concluída | @%s | inseridos=%s | duplicados=%s", target.username, stats.inserted, stats.duplicated)

        except Exception as e:
            self.logger.error("❌ Falha na persistência: %s", e)
            stats.failed = len(comments)
            stats.success = False

        return stats

    async def classify_comments(self, inserted_ids: list[str]) -> ClassifyStats:
        """Classificacao real via AIService. Limitado a 10 por ciclo."""
        stats = ClassifyStats()
        if not inserted_ids:
            return stats

        batch = inserted_ids[:10]
        self.logger.info("[Zyte] Classificando %s/%s comentarios (limite=10)...", len(batch), len(inserted_ids))

        for comment_id in batch:
            try:
                res = self.db.table("comentarios").select("texto_bruto").eq("id", comment_id).single().execute()
                if not res.data:
                    continue
                result = await ai_service.classify_text(res.data["texto_bruto"])
                self.db.table("comentarios").update({
                    "processado_ia": True,
                    "is_hate": result["is_hate"],
                    "categoria_ia": result["categoria_ia"],
                    "confianca_ia": result["confianca_ia"],
                    "evidence_extracted": result["evidencia_lexical"],
                }).eq("id", comment_id).execute()
                stats.classified += 1
            except Exception as e:
                self.logger.error("[Zyte] Falha ao classificar %s: %s", comment_id, e)
                stats.failed += 1

        stats.success = stats.classified > 0
        return stats

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        # Limpa seen_targets a cada ciclo para permitir re-visita de alvos
        self.seen_targets.clear()
        self.seen_queue_ids.clear()

        target = self.claim_next_target()

        if not target:
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="target_claim", simulated=False, error="no_target_available")

        self.logger.info("🎯 Ciclo %s | Alvo: @%s", self.cycle, target.username)

        try:
            # 1. EXTRACAO REAL
            comments = await self.fetch_comments_via_zyte(target)

            source_used = "zyte"
            if not comments:
                self.logger.info("[Zyte] Extracao vazia. Tentando fallback Playwright...")
                try:
                    from core.instagram_headless import InstagramHeadlessScraper
                    headless = InstagramHeadlessScraper()
                    comments = await headless.run(targets=[{"username": target.username}])
                    source_used = "fallback_headless"
                except Exception as fallback_err:
                    self.logger.warning("[Zyte] Fallback headless indisponivel: %s", fallback_err)

            if not comments:
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    target_id=target.candidato_id, source=source_used, extracted=0,
                    simulated=False, error="no_comments_found")

            # 2. PERSISTENCIA REAL
            persist = self.persist_comments(target, comments)

            # 3. CLASSIFICACAO REAL
            classify = await self.classify_comments(persist.inserted_ids)

            result = CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                target=target.username,
                target_id=target.candidato_id,
                source=source_used,
                extracted=len(comments),
                inserted=persist.inserted,
                duplicated=persist.duplicated,
                classified=classify.classified,
                failed=persist.failed + classify.failed,
                db_success=persist.success,
                classifier_success=classify.success,
                simulated=False,
            )

            if result.db_success and (result.inserted + result.duplicated > 0):
                self.queue.mark_candidate_scraped(target)

            return result

        except Exception as exc:
            self.logger.error("[Zyte] Erro critico no ciclo: %s", exc)
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                target_id=target.candidato_id, source=target.source,
                failed=1, error=str(exc)[:200], simulated=False
            )

        finally:
            self.queue.rotate_target(target)
