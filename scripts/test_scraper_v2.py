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
    # Configuração de teste
    target = sys.argv[1] if len(sys.argv) > 1 else "janainacpaschoal"
    max_posts = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    max_comments = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    print(f"[*] Iniciando teste do Scraper V2 para @{target}...")
    print(f"[*] Limite: {max_posts} posts, {max_comments} comentários/post.")

    scraper = InstagramScraperV2(headless=True)
    
    try:
        comments = await scraper.scrape_profile(
            username=target,
            candidato_id="test_id_123",
            max_posts=max_posts,
            max_comments_per_post=max_comments
        )
        
        print(f"\n[OK] Teste concluído!")
        comments_list = comments.get("comments", []) if isinstance(comments, dict) else comments
        print(f"[*] Comentários coletados: {len(comments_list)}")
        
        if comments_list:
            print("[*] Amostra:")
            for i, c in enumerate(comments_list[:3]):
                print(f"  {i}: [{c['autor_username']}] {c['texto_bruto'][:60]}...")
        
        stats = scraper.get_stats()
        print(f"\n[*] Estatísticas: {stats}")
        
    except Exception as e:
        print(f"\n[ERROR] Falha no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper_v2())
