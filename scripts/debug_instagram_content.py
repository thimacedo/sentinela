import asyncio
import os
import json
import base64
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

STORAGE_STATE_PATH = "configs/instagram_storage_state.json"

async def debug_instagram_content():
    if not os.path.exists(STORAGE_STATE_PATH):
        print(f"[ERROR] {STORAGE_STATE_PATH} nao encontrado.")
        return

    username = "raquellyraoficial"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STORAGE_STATE_PATH)
        page = await context.new_page()

        async def handle_response(response):
            url = response.url
            if "graphql" in url or "comments" in url:
                try:
                    data = await response.json()
                    filename = f"scratch/res_{base64.b64encode(url.encode()).decode()[:20]}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"[SAVED] {url} -> {filename}")
                except Exception as e:
                    # print(f"[SKIP] {url}: {e}")
                    pass

        page.on("response", lambda r: asyncio.create_task(handle_response(r)))

        print(f"[*] Acessando post de teste...")
        try:
            # Acessa um post diretamente para simplificar
            shortcode = "DYsnxm0IN5G"
            await page.goto(f"https://www.instagram.com/p/{shortcode}/", wait_until="domcontentloaded", timeout=60000)
            
            # Rolar para baixo para forçar carregamento
            for _ in range(3):
                await page.mouse.wheel(0, 1000)
                await asyncio.sleep(3)
            
            await asyncio.sleep(5)
            print("[*] Concluido.")

        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    asyncio.run(debug_instagram_content())
