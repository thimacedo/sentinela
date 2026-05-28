"""
Script de recuperacao emergencial do INSTAGRAM_SESSIONID da conta principal.
Executa login direto via Playwright e extrai o sessionid dos cookies.
"""
import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def renovar():
    user = os.getenv("IG_USER")
    password = os.getenv("IG_PASS")
    if not user or not password:
        print("ERRO: IG_USER ou IG_PASS nao definidos no .env")
        return

    print(f"Tentando login para: {user}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        await page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

        # Screenshot de diagnostico para ver o que o IG esta mostrando
        import os as _os
        _os.makedirs("logs/evidence", exist_ok=True)
        await page.screenshot(path="logs/evidence/login_debug_conta1.png", full_page=True)
        print(f"Screenshot salvo. URL atual: {page.url}")

        # Aceitar cookies se necessario
        for cookie_txt in ["Aceitar tudo", "Accept All", "Aceitar", "Accept", "Allow all"]:
            try:
                btn = await page.query_selector(f'button:has-text("{cookie_txt}")')
                if btn and await btn.is_visible():
                    await btn.click()
                    print(f"Banner de cookies aceito: {cookie_txt}")
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        # Seletor ampliado para o campo de usuario
        input_selector = (
            'input[name="username"], input[name="email"], '
            'input[aria-label*="usuario"], input[aria-label*="usuário"], '
            'input[aria-label*="user"], input[aria-label*="Phone"], '
            'input[aria-label*="telefone"], input[aria-label*="email"]'
        )
        await page.wait_for_selector(input_selector, timeout=20000)
        await page.type(input_selector, user, delay=120)
        await page.wait_for_selector('input[name="password"], input[type="password"]', timeout=10000)
        await page.type('input[name="password"], input[type="password"]', password, delay=120)
        await page.keyboard.press("Enter")

        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            await page.wait_for_timeout(8000)

        print(f"URL pos-login: {page.url}")

        # Fechar modais pos-login
        for txt in ["Agora nao", "Not Now", "Agora não"]:
            try:
                b = await page.query_selector(f'button:has-text("{txt}")')
                if b:
                    await b.click()
                    await page.wait_for_timeout(2000)
                    print(f"Modal fechado: {txt}")
            except Exception:
                pass

        # Navegar para home para estabilizar contexto
        try:
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)
        except Exception:
            pass

        # Capturar cookies
        cookies = await ctx.cookies()
        sid = next((c["value"] for c in cookies if c["name"] == "sessionid"), None)

        if sid:
            print(f"Novo sessionid extraido: {sid[:25]}...")
            env_path = Path("C:/Projetos/sentinela/.env")
            lines = [l for l in env_path.read_text(encoding="utf-8").splitlines()
                     if not l.startswith("INSTAGRAM_SESSIONID=")]
            lines.append(f"INSTAGRAM_SESSIONID={sid}")
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print("INSTAGRAM_SESSIONID atualizado no .env com sucesso.")
        else:
            print("ERRO: sessionid nao encontrado nos cookies.")
            print(f"URL atual: {page.url}")
            print("Cookies disponiveis:", [c['name'] for c in cookies])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(renovar())
