import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from core.db import db_client
client = db_client.client

print("🔍 Buscando candidatos com partido inconsistente...")

# Trazemos tudo para analisar, ou filtramos as strings
# A API filter do postgrest não tem um "IN" com lowercase fácil, então pegamos tudo (temos poucos milhares)
res = client.table('candidatos').select('id, partido').execute()

updated = 0
for row in res.data:
    p_raw = str(row.get('partido') or '').strip()
    p_upper = p_raw.upper().replace(' ', '')
    
    if p_upper in ['NÃOINFORMADO', 'NAOINFORMADO', 'SEMPARTIDO', 'N/A', 'NONE', 'NULL']:
        new_party = 'Sem Partido'
        if row.get('partido') != new_party:
            client.table('candidatos').update({'partido': new_party}).eq('id', row['id']).execute()
            updated += 1
            print(f"🔄 Atualizado alvo {row['id'][:8]} para 'Sem Partido'")

print(f"✅ Banco normalizado! {updated} perfis ajustados.")
