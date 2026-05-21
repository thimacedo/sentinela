import os
import json
from playwright.async_api import async_playwright

STORAGE_STATE_PATH = "configs/instagram_storage_state.json"

async def validate_storage_state():
    if not os.path.exists(STORAGE_STATE_PATH):
        print(f"⚠️ {STORAGE_STATE_PATH} não encontrado. Fallback não disponível.")
        return False
        
    print(f"✅ Carregando estado de: {STORAGE_STATE_PATH}")
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STORAGE_STATE_PATH)
        page = await context.new_page()
        
        # Teste de navegação
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        
        # Verifica se está logado (procura por botão de login ou seletor de perfil)
        is_logged_in = await page.locator('div[role="button"][aria-label="Opções de conta"]').count() > 0 or \
                       await page.locator('a[href*="/accounts/activity/"]').count() > 0
        
        if is_logged_in:
            print("🚀 Acesso validado com storage_state.")
            return True
        else:
            print("❌ Falha na validação de login. Estado expirado ou inválido.")
            return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(validate_storage_state())
