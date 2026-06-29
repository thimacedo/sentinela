import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def test():
    key = os.getenv("BROWSERACT_API_KEY")
    async with async_playwright() as pw:
        try:
            print("Tentando com token=...")
            browser = await pw.chromium.connect_over_cdp(f"wss://api.browseract.com/connect?token={key}")
            print("Sucesso!")
            await browser.close()
            return
        except Exception as e:
            print(f"Falha token: {e}")

        try:
            print("Tentando com apiKey=...")
            browser = await pw.chromium.connect_over_cdp(f"wss://api.browseract.com/connect?apiKey={key}")
            print("Sucesso!")
            await browser.close()
            return
        except Exception as e:
            print(f"Falha apiKey: {e}")

        try:
            print("Tentando com header...")
            browser = await pw.chromium.connect_over_cdp("wss://api.browseract.com/connect", headers={"Authorization": f"Bearer {key}"})
            print("Sucesso!")
            await browser.close()
            return
        except Exception as e:
            print(f"Falha header: {e}")

if __name__ == "__main__":
    asyncio.run(test())
