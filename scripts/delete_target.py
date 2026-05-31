import sys
sys.path.append('.')
from core.db import db_client

TARGET = "recusabolsonaro"

# Deleta da tabela candidatos
# Primeiro exclui da fila_coleta (referência FK)
res_fila = db_client.client.table("fila_coleta").delete().eq("candidato_id", TARGET).execute()
print("Deleted from fila_coleta:", res_fila)

# Depois exclui o registro de candidatos
res_cand = db_client.client.table("candidatos").delete().eq("username", TARGET).execute()
print("Deleted from candidatos:", res_cand)
