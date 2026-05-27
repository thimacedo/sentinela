import os
import asyncio
from playwright.async_api import async_playwright

STORAGE_STATE_PATH = "configs/instagram_storage_state.json"

async def export_storage_state():
    async with async_playwright() as pw:
        # Abrir navegador headed para login manual
        headless = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("🌐 Indo para o Instagram. Faça login manualmente...")
        await page.goto('https://www.instagram.com/', wait_until='networkidle')
        
        print("\n--- AGUARDANDO LOGIN ---")
        print("Faça o login no navegador aberto e navegue até a página inicial.")
        print("Após confirmar que está logado, volte a este terminal e pressione ENTER.")
        input("Pressione ENTER para salvar o storage_state...")
        
        # Salvar estado completo
        os.makedirs("configs", exist_ok=True)
        await context.storage_state(path=STORAGE_STATE_PATH)
        print(f"✅ Storage state salvo em {STORAGE_STATE_PATH}")
        
        # Validação rápida
        print("Validando acesso à home...")
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        is_logged_in = await page.locator('svg[aria-label="Home"]').count() > 0 or \
                       await page.locator('div[role="button"][aria-label="Opções de conta"]').count() > 0
        
        if is_logged_in:
            print("🚀 Validação concluída com sucesso.")
        else:
            print("⚠️ Validação inconclusiva: página inicial não parece logada.")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(export_storage_state())
