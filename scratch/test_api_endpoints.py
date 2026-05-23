import os
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

# Ajusta path
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client

def test_summary():
    supa = get_supabase_client()
    now_utc = datetime.now(timezone.utc)
    org_id = None # Simula a requisição normal
    
    # 1. Total de Alvos Ativos
    query_c = supa.table('candidatos').select('id', count='exact').eq('status_monitoramento', 'Ativo')
    c_res = query_c.limit(0).execute()
    c = c_res.count if (c_res and c_res.count is not None) else 0
    print("--- TESTE SUMMARY ---")
    print(f"Alvos ativos count: {c}")

    # 3. Volume analisado e alertas
    query_total = supa.table('comentarios').select('id', count='exact')
    query_hate = supa.table('comentarios').select('id', count='exact').eq('is_hate', True)
    
    t_res_total = query_total.limit(1).execute()
    t_res_hate = query_hate.limit(1).execute()
    
    t_lifetime = t_res_total.count if (t_res_total and t_res_total.count is not None) else 0
    h_lifetime = t_res_hate.count if (t_res_hate and t_res_hate.count is not None) else 0
    
    print(f"t_lifetime: {t_lifetime}")
    print(f"h_lifetime: {h_lifetime}")
    
    res_val = round(((t_lifetime - h_lifetime) / t_lifetime) * 100, 1) if t_lifetime > 0 else 100.0
    print(f"Resiliência: {res_val}")
    
def test_temporal_series():
    supa = get_supabase_client()
    window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    res = supa.table('comentarios').select('data_coleta').eq('is_hate', True).gte('data_coleta', window).limit(2000).execute()
    data = res.data or []
    hours = Counter([item['data_coleta'][:13] + ":00:00" for item in data])
    series = sorted([{"hora": h, "alertas": v} for h, v in hours.items()], key=lambda x: x['hora'])
    print("\n--- TESTE TEMPORAL SERIES ---")
    print(f"Registros encontrados na janela: {len(data)}")
    print(f"Série temporal agrupada: {series}")

if __name__ == "__main__":
    test_summary()
    test_temporal_series()
