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

def _get_str_arg(index: int, default: str) -> str:
    if len(sys.argv) <= index:
        return default
    value = str(sys.argv[index]).strip()
    return value or default


def _get_int_arg(index: int, default: int) -> int:
    if len(sys.argv) <= index:
        return default
    try:
        return int(sys.argv[index])
    except (TypeError, ValueError):
        return default


async def test_scraper_v2():
    target = _get_str_arg(1, os.getenv("TEST_SCRAPER_TARGET") or "janainacpaschoal")
    max_posts = _get_int_arg(2, int(os.getenv("TEST_SCRAPER_MAX_POSTS", "3")))
    max_comments = _get_int_arg(3, int(os.getenv("TEST_SCRAPER_MAX_COMMENTS", "10")))

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
        
        stats = scraper.stats
        print(f"\n[*] Estatísticas: {stats}")
        
    except Exception as e:
        print(f"\n[ERROR] Falha no teste: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper_v2())
