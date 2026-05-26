"""
SessionHealer — Renovação Automática de Sessões Instagram (PASA v80.0)

Responsabilidades:
  - Verificar quais sessões estão expiradas/bloqueadas
  - Tentar relogin via Playwright com credenciais do .env
  - Exportar novos sessionids de volta ao .env e ao ambiente
  - Sinalizar ao orquestrador para reinicializar o scraper
"""
import asyncio
import logging
import os
import re
from typing import List, Optional

logger = logging.getLogger("core.autopilot.session_healer")


class SessionHealer:
    """
    Renova sessões Instagram expiradas automaticamente (PASA v80.0).
    Usa Playwright para relogin silencioso quando todas as sessões são inválidas.
    """

    def __init__(self):
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.env_file = os.path.join(os.getcwd(), ".env")

    async def heal(self) -> bool:
        """
        Ponto de entrada principal. Tenta renovar sessões.
        Retorna True se pelo menos uma sessão foi renovada.
        """
        if not self.username or not self.password:
            logger.error("❌ [SessionHealer] INSTAGRAM_USERNAME ou INSTAGRAM_PASSWORD não configurados no .env.")
            return False

        logger.info(f"🔑 [SessionHealer] Tentando relogin para @{self.username}...")

        new_session_id = await self._playwright_login()
        if not new_session_id:
            logger.error("❌ [SessionHealer] Falha no relogin via Playwright.")
            return False

        # Atualiza o .env e o ambiente em memória
        self._write_session_to_env(new_session_id)
        os.environ["INSTAGRAM_SESSIONID"] = new_session_id

        logger.info(f"✅ [SessionHealer] Nova sessão obtida e exportada para .env: {new_session_id[:10]}...")
        return True

    async def _playwright_login(self) -> Optional[str]:
        """Executa o login no Instagram via Playwright e extrai o sessionid."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("❌ [SessionHealer] Playwright não instalado.")
            return None

        session_id = None

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                # Navega para login
                await page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)

                # Preenche credenciais
                await page.fill('input[name="username"]', self.username)
                await asyncio.sleep(1)
                await page.fill('input[name="password"]', self.password)
                await asyncio.sleep(1)
                await page.click('button[type="submit"]')

                # Aguarda redirecionamento pós-login
                await asyncio.sleep(8)

                # Verifica se está logado (não foi redirecionado para /challenge/)
                if "challenge" in page.url or "login" in page.url:
                    logger.error(f"❌ [SessionHealer] Login falhou. URL atual: {page.url}")
                    await browser.close()
                    return None

                # Extrai o sessionid dos cookies
                cookies = await context.cookies()
                for cookie in cookies:
                    if cookie["name"] == "sessionid" and "instagram.com" in cookie.get("domain", ""):
                        session_id = cookie["value"]
                        break

                await browser.close()

        except Exception as e:
            logger.error(f"💥 [SessionHealer] Erro no Playwright login: {e}")
            return None

        if session_id:
            logger.info(f"✅ [SessionHealer] sessionid extraído com sucesso.")
        else:
            logger.error("❌ [SessionHealer] sessionid não encontrado nos cookies pós-login.")

        return session_id

    def _write_session_to_env(self, new_session_id: str) -> None:
        """Sobrescreve o INSTAGRAM_SESSIONID no arquivo .env."""
        if not os.path.exists(self.env_file):
            logger.warning(f"⚠️ [SessionHealer] Arquivo .env não encontrado em {self.env_file}. Pulando escrita.")
            return

        try:
            with open(self.env_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Substitui linha existente ou adiciona nova
            pattern = r'^INSTAGRAM_SESSIONID=.*$'
            new_line = f"INSTAGRAM_SESSIONID={new_session_id}"

            if re.search(pattern, content, re.MULTILINE):
                updated = re.sub(pattern, new_line, content, flags=re.MULTILINE)
            else:
                updated = content.rstrip() + f"\n{new_line}\n"

            with open(self.env_file, "w", encoding="utf-8") as f:
                f.write(updated)

            logger.info(f"✅ [SessionHealer] .env atualizado com nova sessão.")
        except Exception as e:
            logger.error(f"❌ [SessionHealer] Erro ao escrever no .env: {e}")

    def check_sessions_health(self) -> dict:
        """
        Verifica rapidamente quantas sessões do ambiente estão configuradas.
        Não testa validade — apenas conta. Use _verify_session do scraper para teste real.
        """
        sessions = []
        for i in range(1, 11):
            sid = os.getenv(f"INSTAGRAM_SESSIONID_{i}") or (os.getenv("INSTAGRAM_SESSIONID") if i == 1 else None)
            if sid:
                sessions.append(f"SESSION_{i}")

        return {
            "total_configured": len(sessions),
            "session_labels": sessions,
        }
