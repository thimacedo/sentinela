import os
import asyncio
import re
from workers.scrapers.ig_zyte import IGZyteWorker

async def probe_profile(username):
    print(f"📡 Iniciando probe para @{username}...")
    
    worker = IGZyteWorker(worker_id=f"probe_{username}", config={})
    url = f"https://www.instagram.com/{username}/"
    
    # Faz requisição usando o mecanismo de browser do worker
    result = await worker._zyte_request(url, use_browser=True)
    
    if "browserHtml" not in result:
        print(f"❌ Falha ao obter HTML para @{username}: {result}")
        return
        
    html = result["browserHtml"]
    
    # Salvar amostra
    os.makedirs("logs/zyte_samples", exist_ok=True)
    save_path = f"logs/zyte_samples/{username}.html"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"✅ HTML salvo em {save_path} ({len(html)} bytes)")
    
    # Contagem de posts
    posts = re.findall(r'href="/(?:[^/]+/)?(p|reel)/([^/"]+)/"', html)
    unique_shortcodes = set([p[1] for p in posts])
    
    print(f"📊 Posts encontrados (via regex /p/ ou /reel/): {len(unique_shortcodes)}")
    for sc in list(unique_shortcodes)[:5]:
        print(f"  - Shortcode: {sc}")

async def main():
    targets = ["baleia.rossi", "gleisihoffmann"]
    for t in targets:
        await probe_profile(t)

if __name__ == "__main__":
    asyncio.run(main())
