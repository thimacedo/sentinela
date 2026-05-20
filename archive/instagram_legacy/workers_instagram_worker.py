# instagram_worker.py
import sys
import asyncio
import logging
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from workers.core.base_worker import BaseWorker  # Importa o protocolo central do Sentinela

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

class InstagramWorker(BaseWorker):
    """
    Worker oficial de raspagem do Instagram via Playwright Stealth.
    Herda o protocolo Diamond (BaseWorker) para integração com o orquestrador.
    """
    def __init__(self, target_profile: str, max_posts: int = 20):
        super().__init__(name=f"InstagramWorker-{target_profile}")
        self.target_profile = target_profile
        self.profile_url = f"https://www.instagram.com/{target_profile}/"
        self.max_posts = max_posts 
        
        # Credenciais de Sessão (Injeção de Cookie)
        self.session_id = os.getenv("INSTAGRAM_SESSIONID")
        self.ds_user_id = os.getenv("INSTAGRAM_DS_USER_ID")
        self.csrf_token = os.getenv("INSTAGRAM_CSRFTOKEN")

        if not all([self.session_id, self.ds_user_id, self.csrf_token]):
            raise ValueError("❌ Variáveis de sessão do Instagram ausentes no .env")

    async def _inject_cookies(self, context):
        """Injeta a sessão autenticada para burlar o wall de login."""
        await context.add_cookies([
            {"name": "sessionid", "value": self.session_id, "domain": ".instagram.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "Lax"},
            {"name": "ds_user_id", "value": self.ds_user_id, "domain": ".instagram.com", "path": "/", "secure": True},
            {"name": "csrftoken", "value": self.csrf_token, "domain": ".instagram.com", "path": "/", "secure": True}
        ])

    async def _run(self, *args, **kwargs):
        """Método principal exigido pelo BaseWorker. Executa a rotina de raspagem."""
        self.logger.info(f"🚀 Iniciando Playwright Stealth para: {self.target_profile}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR'
            )
            
            await self._inject_cookies(context)
            page = await context.new_page()
            
            # Stealth Patch
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            """)
            
            try:
                # 1. Acessa o Perfil
                await page.goto(self.profile_url, wait_until="domcontentloaded", timeout=30000)
                
                if "login" in page.url:
                    self.logger.error("❌ Sessão expirada ou bloqueada. Fomos redirecionados.")
                    raise Exception("Sessão do Instagram Inválida/Bloqueada")

                # Fecha pop-ups de notificação
                try:
                    await page.click('button:has-text("Agora não"), button:has-text("Not Now")', timeout=2000)
                except Exception:
                    pass

                # 2. Identifica os posts no grid
                selector = 'a[href*="/p/"], a[href*="/reel/"]'
                await page.wait_for_selector(selector, timeout=15000)
                
                post_links = await page.eval_on_selector_all(selector, 'elements => elements.map(el => el.href)')
                
                # Deduplica e limita
                shortcodes = []
                seen = set()
                for link in post_links:
                    parts = link.split("/")
                    for i, part in enumerate(parts):
                        if part in ("p", "reel") and i + 1 < len(parts):
                            sc = parts[i+1]
                            if sc not in seen:
                                seen.add(sc)
                                shortcodes.append(sc)
                
                shortcodes = shortcodes[:self.max_posts]
                self.logger.info(f"✅ Encontrados {len(shortcodes)} posts. Iniciando extração...")

                # 3. Extração Profunda via Modal (Clicando)
                detailed_posts = []
                for index, element in enumerate(await page.query_selector_all(selector)):
                    if index >= self.max_posts:
                        break
                        
                    try:
                        href = await element.get_attribute('href')
                        shortcode = href.strip('/').split('/')[-1]
                        
                        await element.click()
                        await page.wait_for_selector('div[role="dialog"]', timeout=10000)
                        await asyncio.sleep(2) 
                        
                        dialog_element = await page.query_selector('div[role="dialog"]')
                        if dialog_element:
                            # Extrai Data
                            time_element = await dialog_element.query_selector('time')
                            date_str = await time_element.get_attribute('datetime') if time_element else "Unknown"
                            
                            # Extrai Legenda (Tenta H1 primeiro, depois Span)
                            caption = ""
                            h1 = await dialog_element.query_selector('h1')
                            if h1:
                                caption = await h1.inner_text()
                            else:
                                span = await dialog_element.query_selector('div[role="button"] span')
                                if span:
                                    caption = await span.inner_text()

                            # Formato de saída amigável para o Supabase/Pipeline PASA
                            post_data = {
                                "id": shortcode, # ID real do post
                                "shortcode": shortcode,
                                "text": caption.strip(),
                                "timestamp": date_str,
                                "profile": self.target_profile
                            }
                            detailed_posts.append(post_data)
                            self.logger.info(f"🔍 [{index+1}/{len(shortcodes)}] Extraído: {shortcode}")
                        
                        # Fecha modal e delay humano
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(2)

                    except Exception as e:
                        self.logger.warning(f"⚠️ Falha ao extrair post do modal: {e}")
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(2)
                    
                # Retorno dos dados para o Orquestrador
                return detailed_posts

            except Exception as e:
                self.logger.error(f"❌ Erro geral na raspagem: {e}")
                raise  # Levanta o erro para o BaseWorker acionar o handle_failure
            finally:
                await browser.close()

    def handle_failure(self, exception: Exception):
        """Hook de falha do BaseWorker. Aqui podemos integrar alertas ou marcação no Supabase."""
        self.logger.error(f"🚨 ALERTA DE FALHA NO WORKER {self.name}: {str(exception)}")


# Bloco de teste isolado
async def main():
    worker = InstagramWorker("instagram", max_posts=3)
    dados = await worker.execute()
    
    print("\n" + "="*50)
    print("📝 PAYLOAD FINAL PARA O PIPELINE SENTINELA:")
    print("="*50)
    for d in dados: 
        print(f"ID: {d.get('id')} | Data: {d.get('timestamp')}")
        print(f"Texto: {d.get('text')[:100]}...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
