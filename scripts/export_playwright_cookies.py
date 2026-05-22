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
        raise RuntimeError('Variáveis IG_USER e IG_PASS devem estar definidas')

    async with async_playwright() as pw:
        # Executar em modo não headless para evitar bloqueios de detecção
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Verificar se já temos um SESSIONID no .env
        sessionid = os.getenv('INSTAGRAM_SESSIONID')
        if sessionid:
            # Injetar cookie de sessão no contexto
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
            # Navegar para a página principal com timeout maior e tratamento de falha
            try:
                await page.goto('https://www.instagram.com/', wait_until='networkidle', timeout=60000)
            except Exception as e:
                print(f"Aviso: falha ao acessar Instagram com SESSIONID ({e}). Tentando login manual.")
                # Fallback para fluxo antigo de login
                await page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
                if os.getenv('MANUAL_LOGIN') == '1':
                    print('Faça login manualmente no Instagram. Aguardando 10 segundos para concluir...')
                    await asyncio.sleep(10)
                else:
                    # (Reusar código de login automatizado existente após este bloco)
                    pass
            else:
                print('Login por SESSIONID bem-sucedido')
            # Garantir que a página carregou completamente
            try:
                await page.wait_for_load_state('networkidle', timeout=30000)
            except Exception:
                pass
        else:
            # Fluxo antigo (login manual ou automatizado)
            await page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
            if os.getenv('MANUAL_LOGIN') == '1':
                print('Faça login manualmente no Instagram. Aguardando 10 segundos para concluir...')
                await asyncio.sleep(10)
            else:
                # Tentar localizar o campo de usuário; se falhar, clicar no botão "Log in" da página inicial
                try:
                    await page.wait_for_selector('input[name="username"]', timeout=15000)
                except Exception:
                    login_btn = await page.query_selector('a:has-text("Log in")')
                    if login_btn:
                        await login_btn.click()
                        await page.wait_for_selector('input[name="username"]', timeout=30000)
                # Possível banner de consentimento
                try:
                    accept_btn = await page.query_selector('button:has-text("Accept")')
                    if accept_btn:
                        await accept_btn.click()
                except Exception:
                    pass
                # Preencher credenciais
                await page.wait_for_selector('input[name="username"]', timeout=60000)
                await page.fill('input[name="username"]', ig_user)
                await page.fill('input[name="password"]', ig_pass)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle', timeout=60000)
                await asyncio.sleep(5)  # garantir que cookies estejam definidos

        # Capturar cookies com tratamento de falha caso a página tenha sido fechada
        try:
            cookies = await context.cookies()
        except Exception as e:
            # Se a página foi fechada inesperadamente, esperar um pouco e tentar novamente
            print(f"Aviso: falha ao obter cookies ({e}), aguardando e tentando novamente...")
            await asyncio.sleep(5)
            cookies = await context.cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        print('--- COOKIES ---')
        print(cookie_string)

        # Persistir no .env
        env_path = Path('C:/Projetos/sentinela/.env')
        if env_path.exists():
            lines = env_path.read_text(encoding='utf-8').splitlines()
            # remover linhas antigas de INSTAGRAM_COOKIE_FULL
            lines = [ln for ln in lines if not ln.startswith('INSTAGRAM_COOKIE_FULL')]
            lines.append(f'INSTAGRAM_COOKIE_FULL={cookie_string}')
            env_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            print('INSTAGRAM_COOKIE_FULL atualizado no .env')
        else:
            print('.env não encontrado, cookie salvo apenas no log')

        await browser.close()

if __name__ == '__main__':
    asyncio.run(export_cookies())
