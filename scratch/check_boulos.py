import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    print("[*] Detalhando registros de Boulos...")
    try:
        res = supabase.table('candidatos').select('*').ilike('username', '%boulos%').execute()
        res_nome = supabase.table('candidatos').select('*').ilike('nome_completo', '%boulos%').execute()
        
        candidatos = {}
        for r in res.data:
            candidatos[r['id']] = r
        for r in res_nome.data:
            candidatos[r['id']] = r
            
        for cid, cand in candidatos.items():
            print(f"\n--- Registro ID: {cand.get('id')} ---")
            print(f"Nome Completo:  {cand.get('nome_completo')}")
            print(f"Username:       @{cand.get('username')}")
            print(f"Cargo:          {cand.get('cargo')}")
            print(f"Estado:         {cand.get('estado')}")
            print(f"Status:         {cand.get('status_monitoramento')}")
            print(f"Prioridade:     {cand.get('prioridade_coleta')}")
            print(f"Last Scraped:   {cand.get('last_scraped_at')}")
            
    except Exception as e:
        print(f"💥 Erro: {e}")

if __name__ == '__main__':
    main()
