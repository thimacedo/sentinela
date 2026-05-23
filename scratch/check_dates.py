import os
import sys

# Ajusta path para importar core
sys.path.append(os.getcwd())

from core.supabase_service import get_supabase_client
from datetime import datetime, timedelta, timezone

def main():
    supabase = get_supabase_client()
    
    # Busca comentários de ódio
    res = supabase.table("comentarios").select("data_coleta, data_publicacao, is_hate").eq("is_hate", True).execute()
    data = res.data or []
    
    print(f"Total de comentários de ódio: {len(data)}")
    
    if data:
        print("Amostra das datas de coleta:")
        for item in data[:10]:
            print(f"data_coleta: {item.get('data_coleta')}, data_publicacao: {item.get('data_publicacao')}")
            
        # Verifica quantos estão dentro da janela de 48h
        window = datetime.now(timezone.utc) - timedelta(days=2)
        count_in_window = 0
        for item in data:
            dc_str = item.get("data_coleta")
            if dc_str:
                try:
                    # Tenta parsear removendo a parte de timezone ou ajustando para ISO
                    dc = datetime.fromisoformat(dc_str.replace("Z", "+00:00"))
                    if dc >= window:
                        count_in_window += 1
                except Exception as e:
                    print(f"Erro ao parsear data {dc_str}: {e}")
                    
        print(f"Comentários de ódio na janela de 48h (últimos 2 dias): {count_in_window}")
        print(f"Janela de início (48h atrás): {window.isoformat()}")
    else:
        print("Nenhum comentário de ódio encontrado.")

if __name__ == "__main__":
    main()
