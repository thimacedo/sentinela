import asyncio
import json
import logging
import os
import sys
from pprint import pprint
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from core.instagram_scraper_v2 import InstagramScraperV2

async def debug_post():
    username = "vereadorarhalessarn"
    scraper = InstagramScraperV2(headless=True)
    
    # Force single session
    session = scraper.sessions[0]
    print(f"[*] Usando sessão: {session.label}")
    
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        await context.add_cookies([{'name': 'sessionid', 'value': session.session_id, 'domain': '.instagram.com', 'path': '/'}])
        
        page = await context.new_page()
        page.on("response", scraper._handle_response)
        
        print("[*] Indo para perfil...")
        await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        shortcodes = await scraper._extract_shortcodes(page, 1)
        if not shortcodes:
            print("Nenhum post encontrado.")
            return
        
        shortcode = shortcodes[0]
        print(f"[*] Abrindo post {shortcode}...")
        
        opened = await scraper.open_post_modal(page, shortcode)
        if not opened:
            print("Modal não abriu.")
            return
            
        await scraper.scroll_comment_column(page, scroll_amount=800)
        await asyncio.sleep(2)
        
        print("\n--- CAMADA 1 (Network) ---")
        c1 = scraper._parse_captured_json(shortcode)
        print(f"Total: {len(c1)}")
        for c in c1[:2]: print(c)
        
        print("\n--- CAMADA 2 (Scripts) ---")
        c2 = await scraper._extract_from_scripts(page, shortcode)
        print(f"Total: {len(c2)}")
        for c in c2[:2]: print(c)
        
        print("\n--- CAMADA 3 (DOM) ---")
        c3 = await scraper._extract_from_dom(page, shortcode)
        print(f"Total: {len(c3)}")
        for c in c3: print(c)
        
        print("\n--- DUMP DOM SPANS ---")
        spans = await page.evaluate("() => Array.from(document.querySelectorAll('article span[dir=\"auto\"]')).map(s => s.innerText).filter(t => t.length > 2)")
        print(f"Total Spans: {len(spans)}")
        for i, s in enumerate(spans[:20]):
            print(f"{i}: {repr(s)}")
            
        # Tentar outras abordagens de DOM
        print("\n--- DUMP H3 (Possíveis Usernames) ---")
        h3s = await page.evaluate("() => Array.from(document.querySelectorAll('article h3')).map(s => s.innerText)")
        print(f"Total H3: {len(h3s)}")
        for s in h3s[:5]: print(repr(s))
        
        print("\n--- DUMP COMMENT CONTAINERS ---")
        comments_extracted = await page.evaluate("""() => {
            const results = [];
            const h3s = Array.from(document.querySelectorAll('article h3'));
            h3s.forEach(h3 => {
                const username = h3.innerText.trim();
                if (!username) return;
                
                let container = h3;
                for(let i=0; i<5; i++) { if(container.parentElement) container = container.parentElement; }
                
                const spans = Array.from(container.querySelectorAll('span[dir="auto"]'));
                let commentText = null;
                for(let span of spans) {
                    const txt = span.innerText.trim();
                    const isTime = /^[0-9]+[ ]?(h|d|m|w|y|sem|a|s)$/i.test(txt);
                    const isBlacklist = ['Ver tradução', 'Responder'].includes(txt);
                    if (txt && txt !== username && !isTime && !isBlacklist) {
                        commentText = txt;
                        break;
                    }
                }
                if(commentText) {
                    results.push({ autor: username, texto: commentText });
                }
            });
            return results;
        }""")
        print(f"Total Comments Found by Container Logic: {len(comments_extracted)}")
        for c in comments_extracted:
            print(f"[{c['autor']}] {repr(c['texto'])}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_post())
