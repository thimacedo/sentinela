import asyncio
import os
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

STORAGE_STATE_PATH = "configs/instagram_storage_state.json"

async def debug_instagram_network():
    if not os.path.exists(STORAGE_STATE_PATH):
        print(f"[ERROR] {STORAGE_STATE_PATH} nao encontrado.")
        return

    username = "raquellyraoficial" # Alvo de teste

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STORAGE_STATE_PATH)
        page = await context.new_page()

        urls = []
        async def handle_response(response):
            urls.append(response.url)
            if "graphql" in response.url or "comments" in response.url:
                print(f"[NET] {response.url}")

        page.on("response", handle_response)

        print(f"[*] Acessando perfil de @{username}...")
        try:
            await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # Pegar primeiro post
            shortcode = await page.evaluate(r"""
                () => {
                    const a = document.querySelector('a[href*="/p/"], a[href*="/reel/"]');
                    return a ? a.href.match(/\/(p|reel)\/([^\/]+)\//)[2] : null;
                }
            """)
            
            if shortcode:
                print(f"[*] Acessando post: https://www.instagram.com/p/{shortcode}/")
                await page.goto(f"https://www.instagram.com/p/{shortcode}/", wait_until="domcontentloaded", timeout=60000)
                
                # Rolar para baixo para forçar carregamento de comentários
                await page.mouse.wheel(0, 2000)
                await asyncio.sleep(10)
                
                print(f"[*] Total de URLs capturadas: {len(urls)}")
                with open("scratch/urls.txt", "w") as f:
                    for url in urls:
                        f.write(url + "\n")
            else:
                print("[!] Nenhum post encontrado.")

        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    asyncio.run(debug_instagram_network())
