import os
import sys
import psycopg2
from dotenv import load_dotenv

# Força UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Extrai a senha da URL de banco do .env
import re
env_db_url = os.getenv("DATABASE_URL")
password = "NOVA_SENHA"
if env_db_url:
    match = re.search(r"postgresql://postgres:(.*)@db", env_db_url)
    if match:
        password = match.group(1)

DB_URL = f"postgresql://postgres.vhamejkldzxbeibqeqpk:{password}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"

def main():
    if not DB_URL:
        print("❌ [MIGRATION] DATABASE_URL não encontrada no .env.")
        sys.exit(1)

    sql_file = "sql/migration_v80_cloud_control.sql"
    if not os.path.exists(sql_file):
        print(f"❌ [MIGRATION] Arquivo não encontrado: {sql_file}")
        sys.exit(1)

    print(f"🔌 [MIGRATION] Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print(f"📄 [MIGRATION] Lendo e executando: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
            
        cur.execute(sql)
        conn.commit()
        
        print("✅ [MIGRATION] Migração v80 aplicada com sucesso no Supabase remoto!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"💥 [MIGRATION] Erro ao aplicar migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
