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
    print("=== INSPEÇÃO DETALHADA DE POLÍTICAS DE RLS (comentarios) ===")
    res = run_query("""
        SELECT polname, polcmd, polpermissive, polroles, polqual 
        FROM pg_catalog.pg_policy 
        WHERE polrelid = 'comentarios'::regclass
    """)
    if res:
        for p in res:
            is_permissive = "Permissive" if p.get('polpermissive') else "RESTRICTIVE"
            print(f"Policy: {p.get('polname')} | Cmd: {p.get('polcmd')} | Type: {is_permissive} | Roles: {p.get('polroles')}")
    else:
        print("Nenhuma política encontrada ou erro.")

if __name__ == "__main__":
    main()
