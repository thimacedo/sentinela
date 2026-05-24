import asyncio
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())
load_dotenv()

from core.instagram_scraper_v2 import InstagramScraperV2

async def test_integrity():
    # 1. Teste de Perfil Inexistente
    target_404 = "perfil_que_nao_existe_sentinela_999"
    print(f"[*] Testando integridade para perfil inexistente: @{target_404}")
    
    scraper = InstagramScraperV2(headless=True)
    try:
        await scraper.scrape_profile(target_404, "test_404")
    except ValueError as e:
        print(f"✅ Sucesso: Erro capturado corretamente: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {type(e).__name__}: {e}")

    # 2. Teste de Identidade Mismatch (Opcional, difícil simular sem redirect real)
    
if __name__ == "__main__":
    asyncio.run(test_integrity())
