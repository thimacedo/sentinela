import psycopg2

regions = [
    'sa-east-1', 
    'us-east-1', 
    'us-east-2', 
    'us-west-1',
    'us-west-2', 
    'ca-central-1', 
    'eu-west-1',
    'eu-west-2',
    'eu-west-3',
    'eu-central-1',
    'eu-central-2',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-northeast-3',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-south-1',
    'ap-south-2',
    'me-central-1'
]

password = "NOVA_SENHA"
project_id = "vhamejkldzxbeibqeqpk"

print("Iniciando testes de conexão...")
for r in regions:
    url = f"postgresql://postgres.{project_id}:{password}@aws-0-{r}.pooler.supabase.com:6543/postgres"
    print(f"Tentando região: {r}...")
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        print(f"[OK] CONECTADO COM SUCESSO na regiao: {r}!")
        print(f"URL Funcional: {url}")
        conn.close()
        break
    except Exception as e:
        print(f"[ERRO] Falha em {r}: {e}")
