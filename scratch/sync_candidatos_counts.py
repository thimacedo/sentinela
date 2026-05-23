import os
import sys
from collections import Counter

# Ajusta path para importar core
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    print("Iniciando sincronização dos contadores na tabela candidatos...")
    
    # 1. Obter todos os candidatos
    cands = supabase.table("candidatos").select("id, username").execute().data or []
    print(f"Encontrados {len(cands)} candidatos.")
    
    # 2. Obter todas as contagens de comentarios por candidato
    print("Obtendo contagens totais de comentários...")
    res_coms = supabase.table("comentarios").select("candidato_id").execute().data or []
    total_counts = Counter([c["candidato_id"] for c in res_coms if c.get("candidato_id")])
    
    # 3. Obter todas as contagens de comentarios de odio por candidato
    print("Obtendo contagens de comentários de ódio...")
    res_hate = supabase.table("comentarios").select("candidato_id").eq("is_hate", True).execute().data or []
    hate_counts = Counter([c["candidato_id"] for c in res_hate if c.get("candidato_id")])
    
    # 4. Atualizar cada candidato
    for i, cand in enumerate(cands):
        username = cand["username"]
        tot = total_counts.get(username, 0)
        hat = hate_counts.get(username, 0)
        
        # Faz update se necessário
        print(f"[{i+1}/{len(cands)}] Atualizando @{username}: totais={tot}, ódio={hat}")
        try:
            supabase.table("candidatos").update({
                "comentarios_totais_count": tot,
                "comentarios_odio_count": hat
            }).eq("id", cand["id"]).execute()
        except Exception as e:
            print(f"Erro ao atualizar candidato {username}: {e}")
        
    print("Sincronização de contadores concluída com sucesso!")

if __name__ == "__main__":
    main()
