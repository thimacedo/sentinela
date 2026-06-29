import asyncio
from playwright.async_api import async_playwright
import json

async def monitor():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # v94.9: Evita wait_until="networkidle" pois o SSE mantém a conexão aberta
            await page.goto("http://localhost:8001", wait_until="domcontentloaded", timeout=30000)
            
            # Espera os dados carregarem e o heartbeat atualizar
            data_found = False
            for _ in range(30):
                await asyncio.sleep(1)
                heartbeat = await page.inner_text("#heartbeat-text")
                if heartbeat != "--:--:--":
                    data_found = True
                    break
            
            data = {}
            data['api_status'] = await page.inner_text("#local-status")
            data['supa_status'] = await page.inner_text("#supa-status")
            data['heartbeat'] = await page.inner_text("#heartbeat-text")
            data['processados'] = await page.inner_text("#stat-classificados")
            data['fila'] = await page.inner_text("#stat-fila")
            data['risco'] = await page.inner_text("#stat-risco")
            data['custo'] = await page.inner_text("#stat-custo")
            
            # Workers status
            data['voyant_status'] = await page.inner_text("#voyant-status")
            data['ollama_status'] = await page.inner_text("#ia-ollama")
            data['mistral_status'] = await page.inner_text("#ia-mistral")
            
            # Log
            data['last_log'] = await page.inner_text("#last-log")
            data['success'] = data_found
            
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(monitor())
