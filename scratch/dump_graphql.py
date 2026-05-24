import asyncio
import json
import os
import sys
import logging
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())
load_dotenv()

from core.instagram_scraper_v2 import InstagramScraperV2
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dump_graphql")

async def dump_data():
    target = "raquellyraoficial"
    logger.info(f"[*] Iniciando coleta de rede de @{target}...")
    
    scraper = InstagramScraperV2(headless=True)
    session = scraper._get_next_session()
    
    os.makedirs("scratch", exist_ok=True)
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        await context.add_cookies([{
            'name': 'sessionid', 
            'value': session.session_id, 
            'domain': '.instagram.com', 
            'path': '/'
        }])

        page = await context.new_page()
        
        api_responses = []
        
        async def handle_response(response):
            url = response.url
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    api_responses.append({"url": url, "data": data})
                    logger.info(f"[*] Capturado: {url[:100]}...")
            except Exception as e:
                pass

        page.on("response", handle_response)
        
        # Abre perfil
        logger.info(f"[*] Acessando perfil de @{target}...")
        await page.goto(f"https://www.instagram.com/{target}/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        
        # Encontra as postagens na tela
        post_selector = 'a[href*="/p/"], a[href*="/reel/"]'
        posts = await page.query_selector_all(post_selector)
        logger.info(f"[*] Encontrados {len(posts)} elementos de post no DOM.")
        
        if posts:
            first_post = posts[0]
            href = await first_post.get_attribute("href")
            logger.info(f"[*] Clicando no post com link: {href}")
            
            # Clica no post
            await first_post.click()
            await asyncio.sleep(10)
            
            # Tira screenshot do modal aberto
            await page.screenshot(path="scratch/post_modal.png")
            logger.info("[*] Screenshot do modal salvo em scratch/post_modal.png")
            
        await browser.close()
        
        # Salva as respostas
        with open("scratch/captured_api_responses.json", "w", encoding="utf-8") as f:
            json.dump(api_responses, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[OK] {len(api_responses)} chamadas de API salvas em scratch/captured_api_responses.json")

if __name__ == "__main__":
    asyncio.run(dump_data())
