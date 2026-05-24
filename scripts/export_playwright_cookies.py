import os
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv
load_dotenv()

async def renew_account_cookies(browser, account: dict):
    user = account["user"]
    password = account["pass"]
    sid_key = account["sid_key"]
    cookie_key = account["cookie_key"]
    
    print(f"\n[*] Iniciando renovação para conta: {user} (Destino: {sid_key})...")
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    page.set_default_timeout(45000)

    logged_in = False
    
    # 1. Tentar login usando o SESSIONID atual correspondente no .env
    sessionid = os.getenv(sid_key)
    
    if sessionid:
        print(f"Tentando autenticar usando {sid_key} do .env...")
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
            await page.wait_for_timeout(5000)
            current_url = page.url
            
            # Se não fomos para a tela de login, consideramos logado
            login_field_selector = (
                'input[name="username"], input[name="email"], '
                'input[aria-label*="usuario"], input[aria-label*="usuário"], '
                'input[aria-label*="user"], input[aria-label*="Phone"], '
                'input[aria-label*="telefone"]'
            )
            if 'accounts/login' not in current_url and not (await page.query_selector(login_field_selector)):
                print(f'Login por {sid_key} inicial parece bem-sucedido')
                logged_in = True
            else:
                print(f'{sid_key} expirado ou inválido (redirecionado para login).')
        except Exception as e:
            print(f"Erro ao testar {sid_key}: {e}. Tentando fluxo de login.")

    # 2. Se não logou via sessionid, fazer login por formulário com usuário e senha
    if not logged_in:
        print("Iniciando fluxo de login com usuário e senha...")
        try:
            await page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
        except Exception:
            await page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded')

        # Banner de cookies
        try:
            accept_btn = await page.query_selector('button:has-text("Accept"), button:has-text("Aceitar"), button:has-text("Allow all cookies")')
            if accept_btn:
                await accept_btn.click()
                print("Banner de cookies aceito")
        except Exception:
            pass

        # Preencher formulário de login
        try:
            # Seletor combinando username, email, ARIA labels em PT e EN
            input_selector = (
                'input[name="username"], input[name="email"], '
                'input[aria-label*="usuario"], input[aria-label*="usuário"], '
                'input[aria-label*="user"], input[aria-label*="Phone"], '
                'input[aria-label*="telefone"]'
            )
            await page.wait_for_selector(input_selector, timeout=20000)
            
            # Digitação com delay simulando comportamento humano (PASA v52.0)
            await page.type(input_selector, user, delay=150)
            
            # Seletor ultra-resiliente para senha
            password_selector = 'input[name="password"], input[type="password"], input[aria-label*="senha"], input[aria-label*="password"]'
            password_element = await page.query_selector(password_selector)
            
            if not password_element or not await password_element.is_visible():
                print("[*] Layout de login em duas etapas detectado. Avançando...")
                await page.keyboard.press("Enter")
                await asyncio.sleep(4) # Aguarda transição visual
                
            # Preenche o campo de senha com delay humano
            await page.wait_for_selector(password_selector, timeout=15000)
            await page.type(password_selector, password, delay=150)
            
            # Clicar em entrar e esperar navegação
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                await page.keyboard.press("Enter")
                
            # Aguarda a transição de rede pós-login
            try:
                await page.wait_for_load_state("networkidle", timeout=25000)
            except:
                await page.wait_for_timeout(8000)
                
            print("Formulário de login submetido com sucesso")
            logged_in = True
        except Exception as e:
            print(f"Erro ao preencher formulário ou submeter login: {e}")
            try:
                os.makedirs("scratch", exist_ok=True)
                await page.screenshot(path="scratch/login_error.png")
                print("[DIAGNOSTICO] Screenshot do erro de login salvo em scratch/login_error.png")
            except Exception as e_snap:
                print(f"Não foi possível salvar o screenshot: {e_snap}")
            try:
                if 'accounts/login' not in page.url:
                    logged_in = True
            except Exception:
                pass

    # 3. Lidar com telas intermediárias
    if logged_in:
        await page.wait_for_timeout(5000)
        
        # Fechar "Salvar informações de login"
        try:
            save_info_btn = await page.query_selector('button:has-text("Agora não"), button:has-text("Not Now"), button:has-text("Agora No"), div[role="button"]:has-text("Agora não")')
            if save_info_btn:
                await save_info_btn.click()
                print('Modal "Salvar informações de login" fechado')
                await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Aviso ao fechar 'Salvar informações': {e}")

        # Fechar modal de "Ativar notificações"
        try:
            not_now_btn = await page.query_selector('button:has-text("Agora não"), button:has-text("Not Now"), button:has-text("Agora No")')
            if not_now_btn:
                await not_now_btn.click()
                print('Modal de "Ativar notificações" fechado')
                await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Aviso ao fechar 'Ativar notificações': {e}")

        # 4. Capturar cookies e salvar no .env
        cookies = await context.cookies()
        new_sessionid = next((c['value'] for c in cookies if c['name'] == 'sessionid'), None)
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        # Salva no arquivo .env
        env_path = Path('C:/Projetos/sentinela/.env')
        if env_path.exists():
            content = env_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            # Remove chaves antigas correspondentes à conta atual
            lines = [ln for ln in lines if not ln.startswith(f'{sid_key}=')]
            if cookie_key:
                lines = [ln for ln in lines if not ln.startswith(f'{cookie_key}=')]
            
            # Adiciona novas chaves
            if new_sessionid:
                lines.append(f'{sid_key}={new_sessionid}')
                # Também atualiza na memória atual para que a próxima conta não pegue o env desatualizado
                os.environ[sid_key] = new_sessionid
                print(f"Novo {sid_key} extraído e configurado no .env")
                
            if cookie_key:
                lines.append(f'{cookie_key}={cookie_string}')
                os.environ[cookie_key] = cookie_string
                print(f"{cookie_key} atualizado no .env")
                
            env_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            print(f"[OK] {user} atualizado com sucesso no .env.")
        else:
            print('.env não encontrado no caminho padrão')
    else:
        print(f"[ERRO] Não foi possível concluir o login no Instagram para a conta {user}.")

    await context.close()

async def export_cookies():
    # Coleta dinâmica das contas cadastradas no .env
    accounts = []
    
    # Conta 1 (Base)
    if os.getenv('IG_USER') and os.getenv('IG_PASS'):
        accounts.append({
            "user": os.getenv('IG_USER'),
            "pass": os.getenv('IG_PASS'),
            "sid_key": "INSTAGRAM_SESSIONID",
            "cookie_key": "INSTAGRAM_COOKIE_FULL"
        })
        
    # Contas adicionais (ex.: IG_USER_1 / IG_PASS_1 ou IG_USER_2 / IG_PASS_2 até 10)
    for i in range(1, 11):
        u = os.getenv(f'IG_USER_{i}')
        p = os.getenv(f'IG_PASS_{i}')
        if u and p:
            if not any(a["user"] == u for a in accounts):
                next_index = len(accounts) + 1
                sid_key = f"INSTAGRAM_SESSIONID_{next_index}"
                accounts.append({
                    "user": u,
                    "pass": p,
                    "sid_key": sid_key,
                    "cookie_key": None
                })

    if not accounts:
        raise RuntimeError('Nenhuma conta do Instagram (IG_USER / IG_PASS) foi definida no .env')

    print(f"[*] Encontrada(s) {len(accounts)} conta(s) para renovação.")
    
    headless_mode = os.getenv('PLAYWRIGHT_HEADLESS', '1') == '1'
    print(f"Iniciando Playwright (headless={headless_mode})...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless_mode)
        
        # Executa a renovação sequencialmente para cada conta
        for acc in accounts:
            try:
                await renew_account_cookies(browser, acc)
            except Exception as e:
                print(f"💥 Erro na renovação da conta {acc['user']}: {e}")
                
        await browser.close()

if __name__ == '__main__':
    asyncio.run(export_cookies())
