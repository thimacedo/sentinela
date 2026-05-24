import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())
load_dotenv()

# Reconfigura a saída do console no Windows para evitar falhas com acentos e emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from core.instagram_scraper_v2 import scrape_instagram, InstagramScraperV2

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

async def test_scraper_v2():
    target = "raquellyraoficial"
    print(f"[*] Iniciando teste do Scraper V2 para @{target}...")
    
    scraper = InstagramScraperV2(headless=True)
    
    try:
        comments = await scraper.scrape_profile(
            username=target,
            candidato_id="test_id_123",
            max_posts=1,
            max_comments_per_post=10
        )
        
        print(f"\n[OK] Teste concluído!")
        print(f"[*] Comentários coletados: {len(comments)}")
        
        if comments:
            print("[*] Amostra:")
            for i, c in enumerate(comments[:3]):
                print(f"  {i}: [{c['autor_username']}] {c['texto_bruto'][:60]}...")
        
        stats = scraper.get_stats()
        print(f"\n[*] Estatísticas: {stats}")
        
    except Exception as e:
        print(f"\n[ERROR] Falha no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper_v2())
