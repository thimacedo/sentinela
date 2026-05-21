import os
import asyncio
import json
from playwright.async_api import async_playwright

async def export_cookies():
    ig_user = os.getenv('IG_USER')
    ig_pass = os.getenv('IG_PASS')
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.goto('https://www.instagram.com/accounts/login/', wait_until='networkidle')
        
        # Depuração de estrutura
        print("Page content snippet:", (await page.content())[:200])
        
        # Seletores flexíveis
        user_input = page.locator('input[name="username"]')
        pass_input = page.locator('input[name="password"]')
        
        await user_input.wait_for(timeout=10000)
        await user_input.fill(ig_user)
        await pass_input.fill(ig_pass)
        await page.locator('button[type="submit"]').click()
        await page.wait_for_timeout(10000)
        
        cookies = await context.cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        print("--- COOKIES ---")
        print(cookie_string)
        
        # Salvar para uso
        with open("logs/cookies_export.txt", "w") as f:
            f.write(cookie_string)
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(export_cookies())
