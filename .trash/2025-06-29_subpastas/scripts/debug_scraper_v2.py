# scripts/debug_scraper_v2.py
import asyncio
import logging
import os
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("debug")

async def debug_profile(username: str):
    """Diagnóstico completo do scraper"""
    
    async with async_playwright() as pw:
        # Iniciamos headless=True por segurança quando executado pelo IDE, 
        # mas permitimos headless=False se o usuário rodar localmente.
        import os
        is_ide = os.getenv("ANTIGRAVITY_IDE", "false").lower() == "true" or os.getenv("IDE_PROCESS", "") != ""
        headless_mode = True if is_ide else False
        
        logger.info(f"[*] Modo headless: {headless_mode}")
        browser = await pw.chromium.launch(headless=headless_mode)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Adicionar sessão (pegar do .env)
        from dotenv import load_dotenv
        load_dotenv()
        
        session_id = os.getenv("INSTAGRAM_SESSIONID_1") or os.getenv("INSTAGRAM_SESSIONID")
        if session_id:
            await context.add_cookies([{
                'name': 'sessionid',
                'value': session_id,
                'domain': '.instagram.com',
                'path': '/'
            }])
        
        page = await context.new_page()
        
        # 1. Verificar acesso ao perfil
        logger.info(f"📍 Navegando para @{username}...")
        await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
        
        await asyncio.sleep(8)
        
        # 2. Verificar login wall
        current_url = page.url
        logger.info(f"📍 URL atual: {current_url}")
        
        if "login" in current_url:
            logger.error("❌ LOGIN WALL DETECTADO!")
            await browser.close()
            return
        
        # 3. Salvar screenshot do perfil
        os.makedirs("scratch", exist_ok=True)
        await page.screenshot(path=f"scratch/debug_{username}_profile.png")
        logger.info(f"📸 Screenshot salvo: scratch/debug_{username}_profile.png")
        
        # 4. Testar seletores de posts
        logger.info("🔍 Testando seletores de posts...")
        
        # Seletor antigo/nossos links do feed
        old_selector = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')).length
        """)
        logger.info(f"  Seletor (a[href*='/p/']): {old_selector} elementos")
        
        # Seletores alternativos
        article_links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('article a[href]')).length
        """)
        logger.info(f"  Links em <article>: {article_links} elementos")
        
        img_parents = await page.evaluate("""
            () => Array.from(document.querySelectorAll('article img')).map(img => img.closest('a')).filter(Boolean).length
        """)
        logger.info(f"  Imagens com links: {img_parents} elementos")
        
        # 5. Extrair e testar primeiro shortcode
        shortcodes = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]'));
                return links
                    .map(a => {
                        const match = a.href.match(/\\/(p|reel)\\/([^\\/\\?]+)/);
                        return match ? match[2] : null;
                    })
                    .filter(Boolean);
            }
        """)
        
        logger.info(f"📦 Shortcodes extraídos: {shortcodes[:5]}")
        
        if not shortcodes:
            logger.error("❌ NENHUM SHORTCODE ENCONTRADO!")
            
            # Dump do HTML para análise
            html = await page.content()
            with open(f"scratch/debug_{username}_html.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"💾 HTML salvo: scratch/debug_{username}_html.html")
            
            await browser.close()
            return
        
        # 6. Testar abertura do modal
        first_shortcode = shortcodes[0]
        logger.info(f"🎯 Testando modal com shortcode: {first_shortcode}")
        
        selector = f'a[href*="/{first_shortcode}"]'
        element = await page.query_selector(selector)
        
        if not element:
            logger.error(f"❌ Elemento não encontrado com seletor: {selector}")
        else:
            logger.info(f"✅ Elemento encontrado! Clicando...")
            await element.click()
            await asyncio.sleep(7)
            
            # Verificar modal
            modal = await page.evaluate("""
                () => !!document.querySelector('div[role="dialog"]')
            """)
            
            if modal:
                logger.info("✅ MODAL ABERTO COM SUCESSO!")
                await page.screenshot(path=f"scratch/debug_{username}_modal.png")
                logger.info(f"📸 Screenshot do modal: scratch/debug_{username}_modal.png")
                
                # Verificar comentários
                comments_visible = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('span[dir="auto"]')).length
                """)
                logger.info(f"💬 Elementos span[dir='auto'] visíveis no modal: {comments_visible}")
                
            else:
                logger.error("❌ MODAL NÃO ABRIU!")
        
        if not headless_mode:
            logger.info("⏸️ Pausando 10s para inspeção manual...")
            await asyncio.sleep(10)
        
        await browser.close()

if __name__ == "__main__":
    import sys
    # Força a variável de ambiente para que o script saiba que está rodando no IDE
    os.environ["ANTIGRAVITY_IDE"] = "true"
    
    # Testar com um perfil ativo
    asyncio.run(debug_profile("marcelovanhattem"))
