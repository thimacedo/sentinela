import asyncio
import os
import json
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

STORAGE_STATE_PATH = "configs/instagram_storage_state.json"

async def debug_instagram_dom():
    if not os.path.exists(STORAGE_STATE_PATH):
        print(f"[ERROR] {STORAGE_STATE_PATH} nao encontrado.")
        return

    username = "raquellyraoficial" # Alvo de teste

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STORAGE_STATE_PATH)
        page = await context.new_page()

        print(f"[*] Acessando perfil de @{username}...")
        try:
            await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10) # Espera manual para renderizacao
            
            # Dump shortcodes via DOM (teste de seletores atuais)
            shortcodes = await page.evaluate(r"""
                () => Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"], a[href*="/reels/"]'))
                    .map(a => {
                        const match = a.href.match(/\/(p|reel|reels)\/([^\/]+)\//);
                        return match ? match[2] : null;
                    })
                    .filter(Boolean)
            """)
            print(f"[*] Shortcodes encontrados via DOM: {list(dict.fromkeys(shortcodes))}")

            # Dump do HTML para analise de seletores de comentarios se houver posts
            if shortcodes:
                first_post = shortcodes[0]
                print(f"[*] Acessando post: https://www.instagram.com/p/{first_post}/")
                await page.goto(f"https://www.instagram.com/p/{first_post}/", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(10)
                
                # Tentativa de pegar textos de comentarios
                comments = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('span, div'))
                        .map(el => el.innerText.trim())
                        .filter(txt => txt.length > 5)
                        .slice(0, 50)
                """)
                print(f"[*] Amostra de textos encontrados no post (50 primeiros):")
                for i, txt in enumerate(comments):
                    print(f"  {i}: {txt[:100]}...")

                # Salvar dump do HTML para analise manual se necessario
                html = await page.content()
                with open("scratch/instagram_post_dump.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"[*] Dump do HTML salvo em scratch/instagram_post_dump.html")
            else:
                print("[!] Nenhum shortcode encontrado no perfil.")
                html = await page.content()
                with open("scratch/instagram_profile_dump.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("[!] Dump do perfil salvo em scratch/instagram_profile_dump.html")

        except Exception as e:
            print(f"[ERROR] Falha no debug: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    asyncio.run(debug_instagram_dom())
