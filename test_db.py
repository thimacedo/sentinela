import os
import json
import urllib.request
from urllib.error import HTTPError
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL') + '/rest/v1/rpc/exec_sql'
headers = {
    'apikey': os.getenv('SUPABASE_KEY'),
    'Authorization': 'Bearer ' + os.getenv('SUPABASE_KEY'),
    'Content-Type': 'application/json'
}

queries = [
    "ALTER TABLE public.redes_coordenadas ADD COLUMN IF NOT EXISTS nome_rede text;",
    "ALTER TABLE public.redes_coordenadas ADD COLUMN IF NOT EXISTS tipo_coordenacao text;",
    "ALTER TABLE public.redes_coordenadas ADD COLUMN IF NOT EXISTS nodes jsonb;",
    "ALTER TABLE public.redes_coordenadas ADD COLUMN IF NOT EXISTS edges jsonb;",
    "ALTER TABLE public.redes_coordenadas ADD COLUMN IF NOT EXISTS estatisticas jsonb;",
    "ALTER TABLE public.redes_coordenadas ADD COLUMN IF NOT EXISTS score_perigoso integer;"
]

for i, q in enumerate(queries):
    data = json.dumps({'query': q}).encode('utf-8')
    req = urllib.request.Request(url, headers=headers, data=data, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            print(f"SQL {i+1} executado:", response.read().decode('utf-8'))
    except HTTPError as e:
        print(f"Erro SQL {i+1}:", e.read().decode('utf-8'))
