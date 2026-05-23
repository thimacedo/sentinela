import os
import sys

# Ajusta path para importar core
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    # 1. Total de Candidatos
    res_cand = supabase.table("candidatos").select("*", count="exact").execute()
    total_candidatos = len(res_cand.data) if res_cand.data else 0
    print(f"Total de Candidatos no banco: {total_candidatos}")
    
    # 2. Soma de comentarios_totais_count na tabela candidatos
    sum_totais = sum(c.get("comentarios_totais_count", 0) or 0 for c in res_cand.data) if res_cand.data else 0
    sum_odio = sum(c.get("comentarios_odio_count", 0) or 0 for c in res_cand.data) if res_cand.data else 0
    print(f"Soma comentarios_totais_count em candidatos: {sum_totais}")
    print(f"Soma comentarios_odio_count em candidatos: {sum_odio}")
    
    # 3. Total real de registros na tabela comentarios
    res_com = supabase.table("comentarios").select("id", count="exact").limit(1).execute()
    total_comentarios_real = res_com.count
    print(f"Total REAL de Comentários na tabela 'comentarios': {total_comentarios_real}")
    
    # 4. Total real de ódio na tabela comentarios
    res_hate = supabase.table("comentarios").select("id", count="exact").eq("is_hate", True).limit(1).execute()
    total_hate_real = res_hate.count
    print(f"Total REAL de Ódio na tabela 'comentarios' (is_hate = True): {total_hate_real}")

if __name__ == "__main__":
    main()
