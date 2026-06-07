import asyncio
import os
import sys
from playwright.async_api import async_playwright
from pathlib import Path

# Adiciona o root do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import db_client
from core.supabase_service import get_supabase_client

async def refresh_session():
    username = os.getenv('IG_USER')
    password = os.getenv('IG_PASS')
    
    if not username or not password:
        print('Credenciais IG_USER/IG_PASS não encontradas no .env')
        return
        
    async with async_playwright() as pw:
        # Lançamos com headless=False conforme solicitado para resolver desafios
        print(f"🚀 Lançando navegador para reautenticar @{username}...")
        headless = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Navegando para o Instagram...")
            await page.goto('https://www.instagram.com/accounts/login/', timeout=90000)
            
            # Espera um pouco para carregamento de scripts dinâmicos
            await asyncio.sleep(5)
            
            # Tenta fechar diálogos de cookies/consentimento de várias formas
            print("🛡️ Verificando diálogos de consentimento...")
            buttons = [
                'button:has-text("Permitir"), button:has-text("Allow"), button:has-text("Aceitar")',
                'button:has-text("Apenas cookies necessários"), button:has-text("Only allow essential cookies")',
                'div[role="dialog"] button'
            ]
            for selector in buttons:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        print(f"✅ Diálogo fechado com seletor: {selector}")
                        await asyncio.sleep(2)
                except:
                    pass

            print("⌨️ Procurando campos de login...")
            # Tenta encontrar por nome ou por placeholder
            try:
                username_field = page.locator('input[name="username"], input[placeholder*="telefone"], input[placeholder*="Phone"]')
                await username_field.wait_for(state="visible", timeout=45000)
                
                await username_field.fill(username)
                await page.fill('input[name="password"]', password)
                await asyncio.sleep(1)
                await page.click('button[type="submit"]')
                print("🚀 Formulário enviado.")
            except Exception as e:
                print(f"⚠️ Não foi possível preencher automaticamente: {e}")
                print("📸 Salvando screenshot do estado atual...")
                await page.screenshot(path="ig_login_error.png")
                print("👉 Verifique 'ig_login_error.png' para entender o bloqueio.")
                print("⏳ Você tem 2 minutos para intervir manualmente no navegador se ele estiver visível.")
                await asyncio.sleep(120) 
            
            print("⏳ Aguardando redirecionamento pós-login...")
            # Espera o sessionid aparecer nos cookies ou a URL mudar
            for _ in range(30): # 3 minutos (30 * 6s)
                cookies = await context.cookies()
                session_cookie = next((c['value'] for c in cookies if c['name'] == 'sessionid'), None)
                if session_cookie:
                    db_client.client.table('scraping_accounts').upsert({
                        'username': username,
                        'session_id': session_cookie,
                        'status': 'ACTIVE',
                        'last_used_at': 'now()'
                    }, on_conflict='username').execute()
                    print(f'✅ SUCESSO! Novo sessionid salvo: {session_cookie[:20]}...')
                    return
                
                if "login" not in page.url.lower() and "instagram.com" in page.url:
                    print(f"🔗 URL mudou para: {page.url}. Tentando extrair cookies novamente...")
                
                await asyncio.sleep(6)
            
            print("❌ Falha ao obter sessionid após o tempo de espera.")
            await page.screenshot(path="ig_final_state.png")
        
        except Exception as e:
            print(f"❌ Erro durante refresh: {e}")
        finally:
            await asyncio.sleep(5) # Pequena pausa para visualização
            await browser.close()

if __name__ == "__main__":
    asyncio.run(refresh_session())
