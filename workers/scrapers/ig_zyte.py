from __future__ import annotations

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
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self._blocked_slots: set = set()

        self.zyte_key = os.getenv("ZYTE_API_KEY")
        self.zyte_api_url = "https://api.zyte.com/v1/extract"
        self.app_id = "936619743392459"
        self.max_posts = config.get("max_posts", 3)
        self.max_comments_per_post = config.get("max_comments_per_post", 100)
        self.storage_state_path = "configs/instagram_storage_state.json"

    def describe(self) -> str:
        return "Instagram Scraper via Zyte API (Real Extraction v50.1)"

    async def setup(self) -> None:
        if not self.zyte_key:
            self.logger.error("ZYTE_API_KEY nao encontrada no ambiente.")
            raise RuntimeError("zyte_api_key_missing")
        self.logger.info("Motor Zyte configurado e pronto para extracao real.")

    async def teardown(self) -> None:
        self.logger.info("Motor Zyte encerrado.")

    def _build_session_cookie(self) -> tuple[str, str]:
        """
        Retorna (cookie_string, slot_label) priorizando:
        1. INSTAGRAM_COOKIE_FULL
        2. Primeiro INSTAGRAM_SESSIONID* nao bloqueado (sequencial)
        3. sessionid extraido do storage_state
        """
        cookie_full = os.getenv("INSTAGRAM_COOKIE_FULL")
        if cookie_full:
            return cookie_full, "full_cookie"

        session_keys = sorted(k for k in os.environ if k.startswith("INSTAGRAM_SESSIONID"))
        for key in session_keys:
            if key in self._blocked_slots:
                continue
            session_id = os.getenv(key)
            if session_id:
                self.logger.debug("[Zyte] Usando slot=%s", key)
                return f"sessionid={session_id}", key

        if os.path.exists(self.storage_state_path):
            try:
                with open(self.storage_state_path, encoding="utf-8") as f:
                    state = json.load(f)
                for cookie in state.get("cookies", []):
                    if cookie.get("name") == "sessionid" and ".instagram.com" in cookie.get("domain", ""):
                        self.logger.info("[Zyte] Usando sessionid do storage_state")
                        return f"sessionid={cookie['value']}", "storage_state"
            except Exception as e:
                self.logger.warning("[Zyte] Falha ao ler storage_state: %s", e)

        return "", "no_session"

    async def _zyte_request(self, url: str, headers: Dict[str, str] = None, cookies: str = None, use_browser: bool = False) -> Dict[str, Any]:
        """Requisicao via Zyte API com circuit breaker, retentativas e rotacao de sessao."""
        if not zyte_circuit_breaker.can_execute("zyte_api"):
            return {"error": "circuit_open", "status_code": 999}

        session_cookie, current_slot = self._build_session_cookie()
        if session_cookie:
            cookies = f"{session_cookie}; {cookies}" if cookies else session_cookie

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

                if response.status_code in [401, 403]:
                    self.logger.warning("[Zyte] Auth error (HTTP %s) slot=%s", response.status_code, current_slot)
                    self._blocked_slots.add(current_slot)
                    return {"error": "auth_failed", "status_code": response.status_code, "slot": current_slot}

                if response.status_code == 429:
                    self.logger.warning("[Zyte] Rate Limited (429). Backoff...")
                    await asyncio.sleep(10 * (attempt + 1))
                    continue

                if response.status_code == 503:
                    delay = 5 * (2 ** attempt)
                    self.logger.warning("[Zyte] 503 tentativa %s. Retry in %ss...", attempt + 1, delay)
                    await asyncio.sleep(delay)
                    continue

                zyte_circuit_breaker.record_success("zyte_api")

                if response.status_code != 200:
                    self.logger.error("[Zyte] Erro %s: %s", response.status_code, response.text[:200])
                    zyte_circuit_breaker.record_failure("zyte_api", response.status_code)
                    return {"error": "api_error", "status_code": response.status_code}

                res_data = response.json()

                if use_browser:
                    html = res_data.get("browserHtml", "")
                    login_indicators = ["login-form", "Log in to Instagram", "Pagina nao disponivel", "Page Not Found"]
                    if any(ind in html for ind in login_indicators):
                        self.logger.warning("[Zyte] Login Wall detectado slot=%s -- bloqueando", current_slot)
                        self._blocked_slots.add(current_slot)
                        return {"error": "login_required", "statusCode": 401, "slot": current_slot}

                target_status = res_data.get("statusCode", 200)
                if target_status == 404:
                    return {"error": "not_found", "statusCode": 404}

                if use_browser:
                    return {"browserHtml": res_data.get("browserHtml"), "statusCode": target_status}

                body_b64 = res_data.get("httpResponseBody")
                if body_b64:
                    body_content = base64.b64decode(body_b64).decode("utf-8")
                    if body_content.strip().startswith("{"):
                        return json.loads(body_content)
                    return {"raw_body": body_content}

                return {}

            except Exception as e:
                self.logger.error("[Zyte] Erro de conexao slot=%s: %s", current_slot, e)
                return {"error": "connection_error"}

        return {"error": "service_unavailable", "status_code": 503}

    def _extract_json_from_html(self, html: str) -> Dict[str, Any]:
        if not html:
            return {}
        match = re.search(r'window\.__additionalData\["xdt_api__v1__users__web_profile_info"\s*\]\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        match = re.search(r'window\._sharedData\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return {}

    def _extract_from_dom(self, html: str) -> List[Dict[str, Any]]:
        if not html:
            return []
        posts = []
        links = re.findall(r'href="/(?:[^/]+/)?(p|reel)/([^/"]+)/"', html)
        seen_codes: set = set()
        for _, shortcode in links:
            if shortcode not in seen_codes:
                posts.append({"shortcode": shortcode})
                seen_codes.add(shortcode)
                if len(posts) >= self.max_posts:
                    break
        return posts

    async def _fetch_comments_paginated(self, media_id: str, shortcode: str, headers: Dict[str, str], candidato_id: str) -> list[dict]:
        """Coleta comentarios com paginacao via next_min_id. Respeita max_comments_per_post."""
        comments: list[dict] = []
        min_id: Optional[str] = None

        while len(comments) < self.max_comments_per_post:
            url = f"https://www.instagram.com/api/v1/media/{media_id}/comments/"
            if min_id:
                url += f"?min_id={min_id}"

            data = await self._zyte_request(url, headers)
            if data.get("error"):
                self.logger.warning("[Zyte] Paginacao interrompida em %s: %s", shortcode, data["error"])
                break

            raw = data.get("comments", [])
            if not raw:
                break

            for c in raw:
                if len(comments) >= self.max_comments_per_post:
                    break
                comments.append({
                    "id_externo": f"ig_{c.get('pk')}",
                    "texto_bruto": c.get("text"),
                    "autor_username": c.get("user", {}).get("username"),
                    "data_publicacao": datetime.fromtimestamp(c["created_at"], tz=timezone.utc).isoformat() if c.get("created_at") else datetime.now(timezone.utc).isoformat(),
                    "data_coleta": datetime.now(timezone.utc).isoformat(),
                    "post_shortcode": shortcode,
                    "plataforma": "INSTAGRAM",
                    "rede_social": "INSTAGRAM",
                    "candidato_id": candidato_id,
                    "processado_ia": False,
                    "mined": True,
                })

            next_min_id = data.get("next_min_id")
            if not next_min_id or next_min_id == min_id:
                break
            min_id = next_min_id
            self.logger.debug("[Zyte] Paginando %s -> next_min_id=%s (%s coletados)", shortcode, min_id, len(comments))

        self.logger.info("[Zyte] Post %s: %s comentarios coletados", shortcode, len(comments))
        return comments

    async def fetch_comments_via_zyte(self, target: Target) -> list[dict]:
        self.logger.info("[Zyte] Coletando perfil: @%s | max_posts=%s max_comments=%s", target.username, self.max_posts, self.max_comments_per_post)

        profile_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={target.username}"
        headers = {
            "X-IG-App-ID": self.app_id,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }

        data = await self._zyte_request(profile_url, headers)
        user_data = data.get("data", {}).get("user")

        html = ""
        if not user_data:
            self.logger.info("[Zyte] API JSON falhou. Tentando Browser Rendering...")
            browser_url = f"https://www.instagram.com/{target.username}/"
            browser_res = await self._zyte_request(browser_url, {"User-Agent": headers["User-Agent"]}, use_browser=True)
            html = browser_res.get("browserHtml", "")
            if html:
                extracted_data = self._extract_json_from_html(html)
                user_data = (
                    extracted_data.get("data", {}).get("user") or
                    extracted_data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user")
                )

        shortcodes_to_fetch = []
        if user_data:
            edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
            for edge in edges[:self.max_posts]:
                node = edge.get("node", {})
                if node.get("shortcode") and node.get("id"):
                    shortcodes_to_fetch.append({"shortcode": node["shortcode"], "media_id": node["id"]})
        elif html:
            self.logger.info("[Zyte] JSON nao encontrado no HTML. Tentando DOM...")
            for p in self._extract_from_dom(html):
                shortcodes_to_fetch.append({"shortcode": p["shortcode"], "media_id": None})

        if not shortcodes_to_fetch:
            self.logger.warning("[Zyte] Falha ao obter posts do perfil @%s", target.username)
            return []

        all_comments: list[dict] = []
        for item in shortcodes_to_fetch:
            shortcode = item["shortcode"]
            media_id = item["media_id"]
            if not media_id:
                self.logger.info("[Zyte] Post %s sem media_id, pulando.", shortcode)
                continue
            post_comments = await self._fetch_comments_paginated(media_id, shortcode, headers, target.candidato_id)
            all_comments.extend(post_comments)

        return all_comments

    def persist_comments(self, target: Target, comments: list[dict]) -> PersistStats:
        stats = PersistStats()
        if not comments:
            return stats
        sent_ids = {c["id_externo"] for c in comments if c.get("id_externo")}
        try:
            res = self.db.table("comentarios").upsert(
                comments, on_conflict="id_externo", ignore_duplicates=True
            ).execute()
            stats.inserted = len(res.data)
            stats.duplicated = len(sent_ids) - stats.inserted
            stats.inserted_ids = [str(item["id"]) for item in res.data]
            stats.success = True
            self.logger.info("[Zyte] Persistencia | @%s | inseridos=%s | duplicados=%s", target.username, stats.inserted, stats.duplicated)
        except Exception as e:
            self.logger.error("[Zyte] Falha na persistencia: %s", e)
            stats.failed = len(comments)
        return stats

    async def classify_comments(self, inserted_ids: list[str]) -> ClassifyStats:
        """Classificacao via AIService. Limitado a 10 por ciclo."""
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
        self.seen_targets.clear()
        self.seen_queue_ids.clear()

        target = self.queue.claim_next_target(
            self.config, self.seen_queue_ids, self.seen_targets,
            active_targets=getattr(self, "active_targets", None),
        )

        # Limpar slots bloqueados a cada ciclo para evitar bloqueio permanente
        self._blocked_slots.clear()

        if not target:
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="target_claim", simulated=False, error="no_target_available")

        self.logger.info("[Zyte] Ciclo %s | Alvo: @%s", self.cycle, target.username)

        try:
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

            persist = self.persist_comments(target, comments)
            classify = await self.classify_comments(persist.inserted_ids)

            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target=target.username, target_id=target.candidato_id,
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
                failed=1, error=str(exc)[:200], simulated=False,
            )

        finally:
            self.queue.rotate_target(target)
