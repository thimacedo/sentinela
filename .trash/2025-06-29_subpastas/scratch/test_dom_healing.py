import asyncio
import logging
import sys
import os

sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from core.agent_scraper.dom_healing import DOMHealer
from core.ai_service import ai_service

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger("test_dom_healing")

async def main():
    logger.info(f"Providers in ai_service: {[p['name'] for p in ai_service.providers]}")
    logger.info(f"GEMINI_API_KEY from env: {os.getenv('GEMINI_API_KEY')}")
    healer = DOMHealer(ai_service=ai_service)
    
    # 1x1 Transparent pixel PNG in base64
    mock_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    mock_html = "<div class='comments-feed-container'><div class='comment-item-layout'>Amei o post!</div></div>"
    
    logger.info("Executing _vision_heal mock request...")
    result = await healer._vision_heal(
        screenshot_b64=mock_b64,
        html_snippet=mock_html,
        selector_name="comment_container"
    )
    
    logger.info(f"Cura Result: {result}")
    
    if result["success"]:
        logger.info(f"SUCCESS: DOM Healing curou com sucesso. Novo seletor: {result['selector']}")
    else:
        logger.info(f"FAILED: DOM Healing falhou: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
