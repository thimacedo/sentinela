import os
import sys
import json
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
        print(f"Erro ao executar '{query_text[:50]}...': {e}")
        return None

def main():
    # 1. Obter contagem real da tabela comentarios
    count_comentarios = run_query("SELECT COUNT(*) FROM comentarios")
    print("Contagem real de comentarios:", count_comentarios)
    
    # 2. Obter contagem de is_hate = true
    count_hate = run_query("SELECT COUNT(*) FROM comentarios WHERE is_hate = true")
    print("Contagem real de is_hate = true:", count_hate)
    
    # 3. Listar políticas RLS da tabela comentarios
    policies = run_query("""
        SELECT policyname, roles, cmd, qual, with_check 
        FROM pg_policies 
        WHERE tablename = 'comentarios'
    """)
    print("\n=== POLÍTICAS RLS (comentarios) ===")
    print(json.dumps(policies, indent=2))
    
    # 4. Verificar se a RLS está ativa
    rls_status = run_query("""
        SELECT relname, relrowsecurity, relforcerowsecurity 
        FROM pg_class 
        WHERE relname = 'comentarios'
    """)
    print("\n=== STATUS RLS ===")
    print(rls_status)
    
    # 5. Listar contagem agregada por data na tabela comentarios
    hate_48h = run_query("""
        SELECT COUNT(*) 
        FROM comentarios 
        WHERE is_hate = true AND data_coleta >= NOW() - INTERVAL '48 hours'
    """)
    print("\n=== HATE ALERTAS 48H ===")
    print(hate_48h)
    
    # 6. Listar contagens na tabela alertas_ativos se ela existir
    alertas_ativos_exists = run_query("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'alertas_ativos'
        )
    """)
    print("\nTabela alertas_ativos existe?", alertas_ativos_exists)
    if alertas_ativos_exists and alertas_ativos_exists[0].get('exists'):
        count_alertas = run_query("SELECT COUNT(*) FROM alertas_ativos")
        print("Contagem alertas_ativos:", count_alertas)

if __name__ == "__main__":
    main()
