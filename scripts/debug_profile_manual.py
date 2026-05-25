# scripts/debug_profile_manual.py
import asyncio
import logging
import os
import sys
from playwright.async_api import async_playwright
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("debug_manual")

async def debug_profile(username: str):
    """Diagnóstico manual rápido de um perfil específico"""
    load_dotenv()
    
    async with async_playwright() as pw:
        logger.info(f"[*] Iniciando diagnóstico para @{username}...")
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        session_id = os.getenv("INSTAGRAM_SESSIONID_1") or os.getenv("INSTAGRAM_SESSIONID")
        if session_id:
            await context.add_cookies([{
                'name': 'sessionid',
                'value': session_id,
                'domain': '.instagram.com',
                'path': '/'
            }])
        
        page = await context.new_page()
        logger.info(f"📍 Navegando para https://www.instagram.com/{username}/")
        await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(10)
        
        # 1. Verificar Status Geral
        title = await page.title()
        url = page.url
        logger.info(f"📍 URL Atual: {url}")
        logger.info(f"📍 Título da Página: {title}")
        
        if "login" in url:
            logger.error("❌ CAIU NO LOGIN WALL!")
            await browser.close()
            return

        # 2. Verificar se o perfil existe/está disponível
        error_msg = await page.query_selector("h2")
        if error_msg:
            txt = await error_msg.inner_text()
            if "Página não disponível" in txt or "Sorry" in txt:
                logger.error(f"❌ PERFIL INEXISTENTE OU INDISPONÍVEL: {txt}")
                await browser.close()
                return

        # 3. Verificar se é conta privada
        is_private = await page.query_selector("text='Esta conta é privada'") or \
                     await page.query_selector("text='This account is private'")
        if is_private:
            logger.warning("🔒 CONTA PRIVADA! (Não podemos ver os posts)")
        else:
            logger.info("🔓 CONTA PÚBLICA.")

        # 4. Capturar posts e datas
        posts_info = await page.evaluate("""
            () => {
                const results = [];
                const posts = document.querySelectorAll('div._aabd, div._ac7v div');
                posts.forEach((p, i) => {
                    const link = p.querySelector('a');
                    const timeEl = p.querySelector('time');
                    results.push({
                        index: i,
                        href: link ? link.href : null,
                        timestamp: timeEl ? timeEl.getAttribute('datetime') : 'N/A',
                        is_pinned: !!p.querySelector('svg[aria-label*="Pinned"], svg[aria-label*="Fixado"]')
                    });
                });
                return results;
            }
        """)
        
        logger.info(f"📦 Total de posts detectados no grid: {len(posts_info)}")
        for p in posts_info[:5]:
            logger.info(f"   [{p['index']}] Pin: {p['is_pinned']} | Data: {p['timestamp']} | Link: {p['href']}")

        # 5. Screenshot final
        os.makedirs("scratch", exist_ok=True)
        await page.screenshot(path=f"scratch/manual_check_{username}.png")
        logger.info(f"📸 Screenshot salvo em: scratch/manual_check_{username}.png")

        await browser.close()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "alexandre"
    asyncio.run(debug_profile(target))
