import psycopg2
import urllib.parse

passwords = [
    "password",
    "postgres",
    "tempareia102030",
    ",F.C6wK89/S)@4V"
]

project_id = "vhamejkldzxbeibqeqpk"
host = "aws-1-us-east-2.pooler.supabase.com"

print("Testando possíveis senhas...")
for p in passwords:
    escaped_password = urllib.parse.quote_plus(p)
    url = f"postgresql://postgres.{project_id}:{escaped_password}@{host}:5432/postgres"
    print(f"Testando com senha: {p[:3]}***")
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        print(f"[OK] CONECTADO COM SUCESSO! Senha correta: {p}")
        conn.close()
        break
    except Exception as e:
        print(f"[ERRO] Falha: {e}")
