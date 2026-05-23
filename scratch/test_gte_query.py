import os
import sys
from datetime import datetime, timedelta, timezone

# Ajusta path para importar core
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    window = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    print(f"Buscando com window = {window}")
    
    # Query igual a do index.py
    res = supabase.table('comentarios').select('data_coleta').eq('is_hate', True).gte('data_coleta', window).limit(2000).execute()
    data = res.data or []
    print(f"Total de comentários de ódio retornados na query: {len(data)}")
    if data:
        print(f"Amostra: {data[:3]}")

if __name__ == "__main__":
    main()
