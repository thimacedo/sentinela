import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.db import db_client

def cleanup_parties():
    print("Iniciando faxina na base de partidos...")
    
    # 1. Mapeamento de unificação
    mapping = {
        'Sem Partido': 'SEM PARTIDO',
        'Não Informado': 'SEM PARTIDO',
        'N/A': 'SEM PARTIDO',
        'Republicanos': 'REPUBLICANOS',
        'Progressistas': 'PP',
        'Patriota': 'PATRIOTA',
        'SD': 'SOLIDARIEDADE',
        'PCdoB': 'PCDOB',
        'UNIÃO': 'UNIAO',
    }

    # Atualiza as chaves conhecidas
    for old, new in mapping.items():
        res = db_client.client.table('candidatos').update({'partido': new}).eq('partido', old).execute()
        if len(res.data) > 0:
            print(f"  - {old} -> {new}: {len(res.data)} registros atualizados.")

    # 2. Trata NULLs
    null_res = db_client.client.table('candidatos').update({'partido': 'SEM PARTIDO'}).is_('partido', 'null').execute()
    if len(null_res.data) > 0:
        print(f"  - NULL -> SEM PARTIDO: {len(null_res.data)} registros atualizados.")

    # 3. Força UPPERCASE em tudo para evitar "Novo" vs "NOVO"
    all_res = db_client.client.table('candidatos').select('id, partido').execute()
    updates = []
    for cand in all_res.data:
        p = cand.get('partido')
        if p and p != p.upper():
            updates.append({'id': cand['id'], 'partido': p.upper()})
    
    if updates:
        # Batch update (Supabase logic requires multiple calls or a single large list)
        # Using loop for simplicity in this script
        for up in updates:
            db_client.client.table('candidatos').update({'partido': up['partido']}).eq('id', up['id']).execute()
        print(f"  - Normalização para UPPERCASE: {len(updates)} registros ajustados.")

    print("✅ Faxina de partidos concluída.")

if __name__ == "__main__":
    cleanup_parties()
