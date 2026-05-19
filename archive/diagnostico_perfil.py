
import asyncio
import os
from scraper_zyte import InstagramScraperZyte
from dotenv import load_dotenv

load_dotenv()

async def diagnosticar(username):
    print(f"--- Diagnóstico: @{username} ---")
    scraper = InstagramScraperZyte(target_profile=username)
    
    # Tentativa via Browser (que ignora alguns bloqueios de API JSON)
    print(f"Tentando acesso via Browser Rendering...")
    res = await scraper._zyte_request(f"https://www.instagram.com/{username}/", use_browser=True)
    
    html = res.get("browserHtml", "")
    if not html:
        print("Erro: Não foi possível baixar o HTML.")
        return

    # Procura indicadores no HTML
    is_private = "Este perfil é privado" in html or '"is_private":true' in html
    is_login = "Login" in html or "Log in" in html
    
    print(f"Privado detectado: {is_private}")
    print(f"Login exigido: {is_login}")
    
    if is_private:
        print("RESULTADO: O perfil é realmente PRIVADO.")
    elif is_login:
        print("RESULTADO: O perfil é público, mas a SESSÃO/COOKIES expirou.")
    else:
        print("RESULTADO: O perfil deveria ser acessível, verificar Worker.")

if __name__ == "__main__":
    target = input("Digite o username para diagnosticar: ")
    asyncio.run(diagnosticar(target))
