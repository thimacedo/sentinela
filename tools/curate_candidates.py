import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import asyncio
import argparse
import urllib.parse
import re
import httpx
from datetime import datetime, UTC
from pathlib import Path

# Garante path do projeto
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.db import db_client
from core.ai_service import ai_service
from core.intelligence_service import intelligence_service

async def search_web_for_instagram(name: str, cargo: str) -> list:
    query = f"{name} {cargo} instagram oficial"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                raw_handles = re.findall(r'instagram\.com/([a-zA-Z0-9_\.\-]+)', resp.text)
                blacklist = ["p", "developer", "explore", "about", "legal", "terms", "directory", "accounts", "reels", "stories"]
                unique_handles = []
                for h in raw_handles:
                    h_clean = h.lower().strip().replace("/", "").replace("?", "").replace("&", "")
                    if h_clean and h_clean not in blacklist and len(h_clean) > 2:
                        if h_clean not in unique_handles:
                            unique_handles.append(h_clean)
                return unique_handles[:5]
    except Exception as e:
        print(f"⚠️ Erro ao buscar '{name}' no DuckDuckGo: {e}")
    return []

async def discover_best_handle(name: str, cargo: str, web_handles: list) -> str:
    prompt = f"""
    Identifique o nome de usuário (handle) oficial do Instagram da seguinte figura pública brasileira:
    Nome: {name}
    Cargo: {cargo}
    
    Resultados da busca web: {web_handles}
    
    Selecione o handle oficial correto e verídico. Retorne JSON:
    {{
        "username": "handle_correto_ou_vazio",
        "confianca": float (0.0 a 1.0)
    }}
    """
    try:
        res = await ai_service.chat_completion(
            prompt=prompt,
            system_prompt="Você é um assistente especializado em mapear perfis oficiais de políticos brasileiros nas redes sociais.",
            response_format="json_object"
        )
        if res and isinstance(res, dict) and "username" in res:
            username = res["username"].lower().strip().replace("@", "")
            if username and res.get("confianca", 0.0) >= 0.6:
                return username
    except:
        pass
    return web_handles[0] if web_handles else None

async def curate_candidate(c: dict, auto: bool = False):
    username_antigo = c.get("username")
    nome = c.get("nome_completo") or username_antigo
    cargo = c.get("cargo") or "Político"
    
    print(f"\n──────────────────────────────────────────────────")
    print(f"👥 Candidato em Observação: {nome} (Atual: @{username_antigo})")
    print(f"──────────────────────────────────────────────────")
    
    # Busca ativa na web
    web_handles = await search_web_for_instagram(nome, cargo)
    sugestao = await discover_best_handle(nome, cargo, web_handles)
    
    if not sugestao:
        sugestao = username_antigo
        
    print(f"💡 Handle Atual: @{username_antigo}")
    print(f"💡 Handles na Web: {web_handles}")
    print(f"💡 Handle Recomendado por IA: @{sugestao}")
    
    escolha = "1"
    novo_username = sugestao
    
    if not auto:
        print("\nEscolha uma opção:")
        print(f"1) Aceitar recomendação: @{sugestao}")
        print("2) Digitar outro handle manualmente")
        print("3) Desativar candidato (Fora de escopo)")
        print("4) Pular candidato (Manter em Observação)")
        
        try:
            escolha = input("Opção [1-4]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nPulando candidato...")
            return
            
    if escolha == "1":
        novo_username = sugestao
    elif escolha == "2":
        novo_username = input("Digite o handle do Instagram (sem @): ").strip().lower().replace("@", "")
    elif escolha == "3":
        # Desativa no banco
        db_client.client.table("candidatos").update({
            "status_monitoramento": "DESATIVADO",
            "identidade_validada": False,
            "atualizado_em": datetime.now(UTC).isoformat()
        }).eq("username", username_antigo).execute()
        print(f"🚫 Candidato @{username_antigo} desativado com sucesso.")
        return
    else:
        print("⏩ Pulado. Mantido em Observação.")
        return

    # Executa a validação
    print(f"🔎 Validando identidade de @{novo_username} via Instagram Scraper...")
    try:
        # Se mudou o username, remove o antigo para evitar duplicados ou conflitos
        if novo_username != username_antigo:
            db_client.client.table("candidatos").delete().eq("username", username_antigo).execute()
            
        research_res = await intelligence_service.research_and_validate(novo_username)
        
        if research_res and (research_res.get("identidade_validada") is True or research_res.get("status_monitoramento") == "ATIVO"):
            print(f"✅ @{novo_username} validado com sucesso! Inserindo na fila de coleta...")
            # Enfileira
            today = datetime.now(UTC).date().isoformat()
            db_client.client.table("fila_coleta").upsert({
                "candidato_id": novo_username,
                "prioridade": 1, # Fila imediata na curadoria manual
                "status": "PENDENTE",
                "data_agendada": today,
                "updated_at": datetime.now(UTC).isoformat()
            }, on_conflict="candidato_id,data_agendada").execute()
            print(f"🚀 @{novo_username} agendado para coleta imediata.")
        else:
            reason = research_res.get("motivo_desativacao") if research_res else "Erro técnico/timeout"
            print(f"❌ Validação falhou para @{novo_username}. Motivo: {reason}")
            # Se mudou o username mas falhou na validação, podemos recriar o antigo em observação
            if novo_username != username_antigo:
                db_client.client.table("candidatos").upsert({
                    "username": username_antigo,
                    "nome_completo": nome,
                    "cargo": cargo,
                    "status_monitoramento": "Observação",
                    "identidade_validada": None,
                    "atualizado_em": datetime.now(UTC).isoformat()
                }, on_conflict="username").execute()
    except Exception as e:
        print(f"❌ Erro ao validar e registrar: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Ferramenta de Curadoria de Candidatos Sentinela")
    parser.add_argument("--auto", action="store_true", help="Curar automaticamente candidatos usando sugestões de IA")
    args = parser.parse_args()
    
    print("--------------------------------------------------")
    print("🛠️ CURADORIA E TRIAGEM DE CANDIDATOS EM OBSERVAÇÃO")
    print("--------------------------------------------------")
    
    try:
        res = db_client.client.table("candidatos")\
            .select("*")\
            .eq("status_monitoramento", "Observação")\
            .execute()
            
        candidates = res.data or []
        if not candidates:
            print("✨ Nenhum candidato sob status de 'Observação' necessitando curadoria.")
            return
            
        print(f"Encontrados {len(candidates)} candidatos para triagem.")
        
        for c in candidates:
            await curate_candidate(c, auto=args.auto)
            
    except Exception as e:
        print(f"❌ Erro na rotina de curadoria: {e}")

if __name__ == "__main__":
    asyncio.run(main())
