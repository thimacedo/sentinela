from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

STORAGE_STATE_PATH = "configs/instagram_storage_state.json"


def _fetch_probe_target() -> str:
    """Busca o primeiro candidato ativo do Supabase para usar como alvo de probe."""
    try:
        from core.supabase_service import get_supabase_client
        db = get_supabase_client()
        res = db.table("candidatos") \
            .select("username") \
            .eq("status_monitoramento", "Ativo") \
            .order("last_scraped_at", desc=False) \
            .limit(1) \
            .execute()
        if res.data:
            username = res.data[0]["username"]
            print(f"[*] Alvo obtido do Supabase: @{username}")
            return username
    except Exception as e:
        print(f"[WARN] Nao foi possivel buscar alvo do Supabase: {e}")

    print("[FAIL] Nenhum candidato ativo encontrado no Supabase.")
    raise SystemExit(1)


async def validate_storage_state() -> bool:
    if not os.path.exists(STORAGE_STATE_PATH):
        print(f"[WARN] {STORAGE_STATE_PATH} nao encontrado.")
        return False

    probe_username = _fetch_probe_target()

    print(f"[*] Carregando estado de: {STORAGE_STATE_PATH}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=STORAGE_STATE_PATH)
        page = await context.new_page()

        profile_url = f"https://www.instagram.com/{probe_username}/"
        print(f"[*] Abrindo {profile_url} ...")
        await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)

        final_url = page.url
        html = await page.content()

        on_login_page = "/accounts/login" in final_url
        has_login_wall = "Log in" in html and "Don't have an account" in html
        has_profile_content = probe_username in html or "edge_owner_to_timeline_media" in html

        print(f"   URL final  : {final_url}")
        print(f"   Login page : {on_login_page}")
        print(f"   Login wall : {has_login_wall}")
        print(f"   Tem perfil : {has_profile_content}")

        await browser.close()

        if not on_login_page and not has_login_wall and has_profile_content:
            print("[OK] storage_state valido -- perfil acessivel sem login wall.")
            return True

        print("[FAIL] storage_state invalido ou expirado.")
        return False


if __name__ == "__main__":
    asyncio.run(validate_storage_state())
