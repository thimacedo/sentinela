import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def research_posts():
    username = "janainacpaschoal"
    session_id = os.getenv("INSTAGRAM_SESSIONID_1") or os.getenv("INSTAGRAM_SESSIONID")
    
    if not session_id:
        print("❌ Erro: INSTAGRAM_SESSIONID não encontrada.")
        return

    print(f"[*] Usando SID: {session_id[:10]}...")
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies([{
            'name': 'sessionid', 
            'value': session_id, 
            'domain': '.instagram.com', 
            'path': '/'
        }])
        
        page = await context.new_page()
        try:
            print(f"[*] Navegando para @{username}...")
            await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10) # Aguarda renderização JS
        except Exception as e:
            print(f"💥 Erro na navegação: {e}")
            await page.screenshot(path="scratch/research_error.png")
            await browser.close()
            return
        
        # Pesquisa por posts e indicadores de "Fixado"
        posts_data = await page.evaluate("""
            () => {
                const results = [];
                const articles = document.querySelectorAll('article div._ac7v > div._aabd');
                
                // Se não achar pelo seletor específico, tenta genérico
                const gridItems = articles.length > 0 ? articles : document.querySelectorAll('div._aabd');
                
                Array.from(gridItems).slice(0, 12).forEach((item, index) => {
                    const link = item.querySelector('a');
                    const href = link ? link.href : null;
                    const shortcode = href ? href.match(/\\/p\\/([^/]+)\\//)?.[1] : null;
                    
                    // Procura por ícone de pin (geralmente um SVG dentro do container do post)
                    const hasPinIcon = !!item.querySelector('svg[aria-label*="Pinned"], svg[aria-label*="Fixado"]');
                    
                    // Tenta encontrar texto "Fixado" ou similar
                    const hasPinText = item.innerText.includes('Fixado') || item.innerText.includes('Pinned');
                    
                    results.push({
                        index,
                        shortcode,
                        is_pinned: hasPinIcon || hasPinText,
                        html_snippet: item.innerHTML.substring(0, 500) // Para análise
                    });
                });
                return results;
            }
        """)
        
        for p in posts_data:
            status = "[FIXADO]" if p['is_pinned'] else "[NORMAL]"
            print(f"{p['index']}: {status} {p['shortcode']}")
            if p['is_pinned']:
                print(f"    Snippet: {p['html_snippet'][:200]}...")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(research_posts())
