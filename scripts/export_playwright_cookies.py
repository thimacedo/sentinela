import os
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv
load_dotenv()

async def export_cookies():
    ig_user = os.getenv('IG_USER')
    ig_pass = os.getenv('IG_PASS')
    if not ig_user or not ig_pass:
        raise RuntimeError('Variáveis IG_USER e IG_PASS devem estar definidas no .env')

    headless_mode = os.getenv('PLAYWRIGHT_HEADLESS', '1') == '1'
    print(f"Iniciando Playwright (headless={headless_mode})...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless_mode)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Configurar timeout padrão
        page.set_default_timeout(45000)

        # 1. Tentar login usando o SESSIONID atual do .env
        sessionid = os.getenv('INSTAGRAM_SESSIONID')
        logged_in = False

        if sessionid:
            print("Tentando autenticar usando INSTAGRAM_SESSIONID do .env...")
            cookie = {
                'name': 'sessionid',
                'value': sessionid,
                'domain': '.instagram.com',
                'path': '/',
                'expires': -1,
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Lax'
            }
            await context.add_cookies([cookie])
            try:
                await page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
                # Esperar um pouco para ver se redireciona
                await page.wait_for_timeout(5000)
                current_url = page.url
                
                # Se não fomos para a tela de login, consideramos logado
                if 'accounts/login' not in current_url and not (await page.query_selector('input[name="username"]')):
                    print('Login por SESSIONID inicial parece bem-sucedido')
                    logged_in = True
                else:
                    print('SESSIONID expirado ou inválido (redirecionado para login).')
            except Exception as e:
                print(f"Erro ao testar SESSIONID: {e}. Tentando fluxo de login.")

        # 2. Se não logou via sessionid, fazer login por formulário
        if not logged_in:
            print("Iniciando fluxo de login com usuário e senha...")
            try:
                await page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
            except Exception:
                await page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded')

            # Banner de consentimento / cookies
            try:
                accept_btn = await page.query_selector('button:has-text("Accept"), button:has-text("Aceitar"), button:has-text("Allow all cookies")')
                if accept_btn:
                    await accept_btn.click()
                    print("Banner de cookies aceito")
            except Exception:
                pass

            # Preencher formulário de login
            try:
                await page.wait_for_selector('input[name="username"]', timeout=20000)
                await page.fill('input[name="username"]', ig_user)
                await page.fill('input[name="password"]', ig_pass)
                
                # Clicar em entrar e esperar navegação
                await asyncio.gather(
                    page.wait_for_navigation(wait_until='networkidle', timeout=60000),
                    page.click('button[type="submit"]')
                )
                print("Formulário de login submetido com sucesso")
                logged_in = True
            except Exception as e:
                print(f"Erro ao preencher formulário ou submeter login: {e}")
                # Forçar clique caso wait_for_navigation tenha falhado mas o login tenha ocorrido
                try:
                    if 'accounts/login' not in page.url:
                        logged_in = True
                except Exception:
                    pass

        # 3. Lidar com telas intermediárias (ex: Salvar informações de login, Notificações)
        if logged_in:
            await page.wait_for_timeout(5000)
            
            # Tentar fechar "Salvar informações de login" ("Agora não" / "Not Now")
            try:
                save_info_btn = await page.query_selector('button:has-text("Agora não"), button:has-text("Not Now"), button:has-text("Agora No"), div[role="button"]:has-text("Agora não")')
                if save_info_btn:
                    await save_info_btn.click()
                    print('Modal "Salvar informações de login" fechado')
                    await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Aviso ao tentar fechar 'Salvar informações': {e}")

            # Tentar fechar modal de "Ativar notificações"
            try:
                not_now_btn = await page.query_selector('button:has-text("Agora não"), button:has-text("Not Now"), button:has-text("Agora No")')
                if not_now_btn:
                    await not_now_btn.click()
                    print('Modal de "Ativar notificações" fechado')
                    await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Aviso ao tentar fechar 'Ativar notificações': {e}")

            # 4. Capturar cookies e salvar no .env
            cookies = await context.cookies()
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            print('--- COOKIES FORMATADOS ---')
            print(cookie_string)

            # Salvar no .env
            env_path = Path('C:/Projetos/sentinela/.env')
            if env_path.exists():
                lines = env_path.read_text(encoding='utf-8').splitlines()
                lines = [ln for ln in lines if not ln.startswith('INSTAGRAM_COOKIE_FULL')]
                
                # Também atualizar o INSTAGRAM_SESSIONID se um novo foi gerado
                new_sessionid = next((c['value'] for c in cookies if c['name'] == 'sessionid'), None)
                if new_sessionid:
                    lines = [ln for ln in lines if not ln.startswith('INSTAGRAM_SESSIONID=')]
                    lines.append(f'INSTAGRAM_SESSIONID={new_sessionid}')
                    print(f"Novo INSTAGRAM_SESSIONID extraído e configurado no .env")

                lines.append(f'INSTAGRAM_COOKIE_FULL={cookie_string}')
                env_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
                print('INSTAGRAM_COOKIE_FULL atualizado com sucesso no .env')
            else:
                print('.env não encontrado no caminho padrão')
        else:
            print("Não foi possível concluir o login no Instagram. Cookies não exportados.")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(export_cookies())
