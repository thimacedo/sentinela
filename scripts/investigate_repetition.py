import asyncio
from core.supabase_service import get_supabase_client
import json

async def investigate():
    supa = get_supabase_client()
    text = "Parabéns Kim Kataguiri 👏👏👏👏"
    
    try:
        # First, try to get just one row to see all columns
        res_sample = supa.table("comentarios").select("*").limit(1).execute()
        if res_sample.data:
            print("--- SCHEMA SAMPLE ---")
            print(list(res_sample.data[0].keys()))
            print("---------------------")

        # 1. Busca ocorrências no banco (sem usar datas por enquanto)
        res = supa.table("comentarios").select("id, autor_username, candidato_id, texto_bruto").eq("texto_bruto", text).execute()
        count = len(res.data) if res.data else 0
        
        details = res.data if res.data else []
        
        result = {
            "search_text": text,
            "database_count": count,
            "occurrences": details
        }
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(investigate())