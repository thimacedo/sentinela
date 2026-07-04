# Worker Session Self-Healing (WkSessaoAutonoma)
# Arquivo: workers/sre/wk_sessao_autonoma.py

import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from playwright.async_api import async_playwright

from workers.base.worker_base import BaseWorker, WorkerMetrics
from workers.base.cycle_result import CycleResult
from core.supabase_client import get_supabase_client
from core.ntfy import NtfyNotifier

logger = logging.getLogger("worker.sessao_autonoma")

class WkSessaoAutonoma(BaseWorker):
    """
    Worker de SRE que monitora e cura automaticamente sessões bloqueadas ou expiradas do Instagram.
    Tenta renovar cookies via login automatizado (Playwright headless) usando credenciais
    da tabela scraping_accounts do Supabase.
    """
    def __init__(self, worker_id: str = "sre-sessao-01", config: Optional[dict] = None):
        super().__init__(worker_id, config or {})
        ntfy_url = os.getenv("NTFY_URL") or "https://ntfy.sh/sentinela-alertas"
        self.ntfy = NtfyNotifier(ntfy_url, enabled=True)
        self.db = None

    async def setup(self) -> None:
        self.logger.info("[SessionHealer] Setup inicializado.")
        try:
            self.db = get_supabase_client()
        except Exception as e:
            self.logger.error(f"[SessionHealer] Erro ao obter cliente Supabase no setup: {e}")

    async def run_cycle(self) -> "CycleResult":
        self.logger.info("[SessionHealer] Iniciando verificação de integridade das contas de scraping.")
        
        result = CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            db_success=True
        )

        if self.db is None:
            try:
                self.db = get_supabase_client()
            except Exception as e_db:
                self.logger.error(f"[SessionHealer] Erro ao obter cliente Supabase: {e_db}")
                result.error = "db_connection_error"
                return result

        try:
            # 1. Busca todas as contas da tabela scraping_accounts do Supabase
            res = await asyncio.to_thread(
                self.db.table("scraping_accounts").select("*").execute
            )
            accounts = res.data or []
        except Exception as e:
            self.logger.error(f"[SessionHealer] Erro ao buscar contas de scraping do Supabase: {e}")
            result.error = "db_connection_error"
            return result

        if not accounts:
            self.logger.info("[SessionHealer] Nenhuma conta cadastrada na tabela scraping_accounts.")
            return result

        self.logger.info(f"[SessionHealer] Analisando {len(accounts)} contas de scraping cadastradas.")
        
        for acc in accounts:
            username = acc.get("username")
            status = acc.get("status")
            password = acc.get("password")
            failures_count = acc.get("failures_count", 0)
            
            # Se a conta está marcada como ativa, ou em cooldown temporário,
            # nós testamos e tentamos renovar se estiver bloqueada ou com falhas consecutivas
            need_heal = status in ("BLOCKED", "COOLDOWN") or failures_count >= 3
            
            if not need_heal:
                # Opcional: testar cookies da conta ativa de forma leve fazendo uma request head?
                # Por ora, focamos em curar as contas marcadas como inoperantes ou com muitas falhas
                continue

            if not password:
                self.logger.warning(f"[SessionHealer] Conta @{username} precisa de cura, mas não possui senha salva no banco. Pulando.")
                continue

            self.logger.info(f"[SessionHealer] Iniciando rotina de cura/login para @{username}...")
            
            # 2. Tenta fazer login automatizado no Playwright
            login_success = False
            new_session_id = None
            error_msg = "unknown_error"

            try:
                login_success, new_session_id, error_msg = await self._attempt_instagram_login(username, password)
            except Exception as e_login:
                self.logger.error(f"[SessionHealer] Excecao inesperada ao logar @{username}: {e_login}")
                error_msg = f"exception_{type(e_login).__name__}"

            now_iso = datetime.now(timezone.utc).isoformat()
            
            if login_success and new_session_id:
                self.logger.info(f"✨ [SessionHealer] Conta @{username} curada com sucesso! Novo sessionid gerado.")
                try:
                    # Atualiza conta para ACTIVE no Supabase
                    await asyncio.to_thread(
                        self.db.table("scraping_accounts").update({
                            "session_id": new_session_id,
                            "status": "ACTIVE",
                            "failures_count": 0,
                            "cooldown_until": None,
                            "last_used_at": now_iso,
                            "updated_at": now_iso
                        }).eq("username", username).execute
                    )
                    
                    await self.ntfy.send(
                        title="Sentinela — Conta Curada",
                        message=f"A conta de scraping @{username} foi re-autenticada com sucesso pelo SessionHealer.",
                        priority="high",
                        tags=["white_check_mark", "key"]
                    )
                    result.inserted += 1
                except Exception as e_up:
                    self.logger.error(f"[SessionHealer] Falha ao persistir nova sessao para @{username}: {e_up}")
                    result.failed += 1
            else:
                # Login falhou: incrementa falhas e estende quarentena
                new_failures = failures_count + 1
                new_status = "BLOCKED" if new_failures >= 3 else "COOLDOWN"
                cooldown_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
                
                self.logger.warning(f"❌ [SessionHealer] Falha na cura de @{username}: {error_msg}. Status: {new_status} (Falha #{new_failures})")
                
                try:
                    await asyncio.to_thread(
                        self.db.table("scraping_accounts").update({
                            "status": new_status,
                            "failures_count": new_failures,
                            "cooldown_until": cooldown_time,
                            "updated_at": now_iso
                        }).eq("username", username).execute
                    )
                    
                    if new_failures >= 3:
                        await self.ntfy.send(
                            title="Sentinela — Conta Bloqueada",
                            message=f"Cura automatica falhou 3x para @{username}: {error_msg}. Conta bloqueada para analise.",
                            priority="urgent",
                            tags=["alarm_clock", "warning"]
                        )
                    result.failed += 1
                except Exception as e_up:
                    self.logger.error(f"[SessionHealer] Falha ao atualizar falhas para @{username}: {e_up}")

        return result

    async def _attempt_instagram_login(self, username: str, password: str) -> tuple[bool, Optional[str], str]:
        """Tenta logar no Instagram Web via Playwright headless e extrair o sessionid."""
        async with async_playwright() as p:
            # Configura o browser headless com tamanho de tela típico
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                self.logger.info(f"[SessionHealer] Acessando tela de login do Instagram para @{username}...")
                await page.goto("https://www.instagram.com/accounts/login/", timeout=60000, wait_until="networkidle")
                
                # Aguarda inputs de login
                await page.wait_for_selector('input[name="username"]', timeout=15000)
                
                # Preenche as credenciais
                await page.fill('input[name="username"]', username)
                await page.fill('input[name="password"]', password)
                
                # Clica em submit
                await page.click('button[type="submit"]')
                self.logger.info(f"[SessionHealer] Formulario enviado. Aguardando autenticacao...")
                
                # Aguarda redirecionamento ou cookie
                success = False
                session_id = None
                error_reason = "timeout"
                
                # Loop rápido para inspecionar cookies a cada 1 segundo por até 20 segundos
                for _ in range(20):
                    await asyncio.sleep(1)
                    cookies = await context.cookies()
                    sid_cookie = next((c for c in cookies if c["name"] == "sessionid"), None)
                    if sid_cookie:
                        session_id = sid_cookie["value"]
                        success = True
                        break
                    
                    # Detecta desafios visuais/2FA
                    if await page.query_selector('input[name="verificationCode"]'):
                        error_reason = "2fa_required"
                        break
                    if "challenge" in page.url:
                        error_reason = "checkpoint_challenge"
                        break
                    if await page.query_selector('p[role="alert"]'):
                        error_reason = "invalid_credentials_alert"
                        break

                await browser.close()
                return success, session_id, error_reason if not success else "success"
                
            except Exception as e:
                self.logger.error(f"[SessionHealer] Erro no fluxo do Playwright para @{username}: {e}")
                await browser.close()
                return False, None, f"playwright_error_{type(e).__name__}"

    async def teardown(self) -> None:
        self.logger.info("[SessionHealer] Teardown finalizado.")

    def describe(self) -> str:
        return "Gerenciador de Cura de Sessoes (Session Self-Healing)"
