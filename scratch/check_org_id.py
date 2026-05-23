import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ajusta path
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client

def run_query(query_text):
    supabase = get_supabase_client()
    try:
        res = supabase.rpc("exec_sql", {"query": query_text}).execute()
        return res.data
    except Exception as e:
        print(f"Erro: {e}")
        return None

def main():
    print("=== DISTRIBUIÇÃO DE ORGANIZATION_ID EM COMENTARIOS ===")
    res_org = run_query("SELECT organization_id, COUNT(*) FROM comentarios GROUP BY organization_id")
    print(res_org)
    
    print("\n=== DISTRIBUIÇÃO DE ORGANIZATION_ID EM CANDIDATOS ===")
    res_cand = run_query("SELECT organization_id, COUNT(*) FROM candidatos GROUP BY organization_id")
    print(res_cand)
    
    print("\n=== COMENTÁRIOS DE ÓDIO (is_hate = true) ===")
    res_hate = run_query("SELECT organization_id, COUNT(*) FROM comentarios WHERE is_hate = true GROUP BY organization_id")
    print(res_hate)

if __name__ == "__main__":
    main()
