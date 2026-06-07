""" PASA v40 - Threat Profiler: Calcula Densidade e Exporta JSON para o Frontend """
import json
import os
import sys
from datetime import datetime

# Ajuste de path para encontrar core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

try:
    from core.db import db_client as db
except ImportError:
    # Se rodar de dentro de scripts
    from core.db import db_client as db

STREAM_FILE = "docs/profiler_stream.json"
KPI_FILE = "docs/kpis.json"

def calculate_hate_density():
    if not db.client:
        print("Erro: Supabase client não inicializado.")
        return

    candidates = db.client.table('candidatos').select('id, username, comentarios_odio_count, comentarios_totais_count').execute()
    
    if not candidates.data:
        print("Nenhum candidato encontrado.")
        return

    stream_data = []
    total_targets = 0
    total_alerts = 0
    total_sample = 0

    for cand in candidates.data:
        username = cand['username']
        total_comments_res = db.client.table('comentarios').select('id', count='exact').eq('candidato_id', username).execute()
        from core.constants import HATE_CATEGORIES
        hate_comments_res = db.client.table('comentarios').select('id', count='exact').eq('candidato_id', username).in_('categoria_ia', HATE_CATEGORIES).execute()
        
        total = total_comments_res.count if total_comments_res.count is not None else 0
        hate = hate_comments_res.count if hate_comments_res.count is not None else 0
        
        if total == 0:
            continue
            
        density = round((hate / total) * 100, 2)
        
        db.client.table('candidatos').update({
            'comentarios_totais_count': total,
            'comentarios_odio_count': hate,
            'nota_relevancia': density
        }).eq('id', cand['id']).execute()
        
        total_targets += 1
        total_alerts += hate
        total_sample += total
        
        stream_data.append({
            "user": username,
            "total": total,
            "hate": hate,
            "density": density,
            "updated_at": datetime.now().isoformat()
        })

    os.makedirs('docs', exist_ok=True)
    
    with open(STREAM_FILE, 'w', encoding='utf-8') as f:
        json.dump(stream_data, f, indent=2)
        
    with open(KPI_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "targets": total_targets,
            "alerts": total_alerts,
            "db_sample": total_sample,
            "updated_at": datetime.now().isoformat()
        }, f)
        
    print(f"Sucesso: {total_targets} alvos processados. JSONs exportados.")

if __name__ == "__main__":
    calculate_hate_density()
