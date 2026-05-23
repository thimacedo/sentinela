import os
import sys

# Ajusta path
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    # 1. Usando count='exact' sem limit
    res_no_limit = supabase.table('comentarios').select('id', count='exact').execute()
    count_no_limit = res_no_limit.count
    data_len_no_limit = len(res_no_limit.data) if res_no_limit.data else 0
    
    # 2. Usando count='exact' com limit(1)
    res_limit_1 = supabase.table('comentarios').select('id', count='exact').limit(1).execute()
    count_limit_1 = res_limit_1.count
    data_len_limit_1 = len(res_limit_1.data) if res_limit_1.data else 0
    
    # 3. Usando count='exact' com limit(0)
    res_limit_0 = supabase.table('comentarios').select('id', count='exact').limit(0).execute()
    count_limit_0 = res_limit_0.count
    
    print(f"Método 1 (Sem limit): count={count_no_limit}, rows={data_len_no_limit}")
    print(f"Método 2 (Limit 1): count={count_limit_1}, rows={data_len_limit_1}")
    print(f"Método 3 (Limit 0): count={count_limit_0}")
    
    # Vamos ver quantos registros a tabela candidatos tem
    res_cand = supabase.table('candidatos').select('id', count='exact').eq('status_monitoramento', 'Ativo').execute()
    print(f"Candidatos ativos: count={res_cand.count}, rows={len(res_cand.data) if res_cand.data else 0}")
    
if __name__ == "__main__":
    main()
