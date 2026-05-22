"""
Diagnostico: renderiza post do Instagram com cookies via Zyte browser
e salva o HTML para analise.
"""
import asyncio
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()
import httpx


async def debug_browser():
    zyte_key = os.getenv("ZYTE_API_KEY")
    cookie_full = os.getenv("INSTAGRAM_COOKIE_FULL", "")

    # Parsear cookies para o formato requestCookies do Zyte
    request_cookies = []
    for pair in cookie_full.split(";"):
        pair = pair.strip()
        if "=" in pair:
            name, value = pair.split("=", 1)
            request_cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".instagram.com",
            })

    print(f"Cookies parseados: {len(request_cookies)}")

    payload = {
        "url": "https://www.instagram.com/p/DYp6eXmtFlf/",
        "browserHtml": True,
        "javascript": True,
        "requestCookies": request_cookies,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.zyte.com/v1/extract",
            auth=(zyte_key, ""),
            json=payload,
        )

    print(f"Status: {resp.status_code}")
    data = resp.json()
    html = data.get("browserHtml", "")
    print(f"HTML length: {len(html)}")

    # Salva HTML para analise
    with open("c:/Projetos/sentinela/scratch/debug_post.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML salvo em scratch/debug_post.html")

    # Verifica login wall
    login_signs = ["Log in", "login-form", "Entrar", "Log In"]
    for sign in login_signs:
        if sign in html:
            print(f"LOGIN WALL: encontrado '{sign}'")

    # Busca textos de comentarios via regex
    texts = re.findall(r'"text"\s*:\s*"([^"]{5,})"', html)
    print(f"Textos encontrados com regex 'text': {len(texts)}")
    for t in texts[:5]:
        print(f"  -> {t[:100]}")

    usernames = re.findall(r'"username"\s*:\s*"([^"]+)"', html)
    print(f"Usernames encontrados: {len(usernames)}")
    for u in usernames[:10]:
        print(f"  -> @{u}")

    # Busca edge_media_to_parent_comment
    if "edge_media_to_parent_comment" in html:
        print("ENCONTRADO: edge_media_to_parent_comment (JSON de comentarios presente)")
    elif "edge_media_to_comment" in html:
        print("ENCONTRADO: edge_media_to_comment (JSON de comentarios presente)")
    else:
        print("NAO encontrado JSON de comentarios no HTML")


if __name__ == "__main__":
    asyncio.run(debug_browser())
