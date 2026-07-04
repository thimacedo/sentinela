import os
import sys
import psycopg2
from dotenv import load_dotenv

# Força UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def main():
    if not DB_URL:
        print("❌ [MIGRATION] DATABASE_URL não encontrada no .env.")
        sys.exit(1)

    try:
        print("🔌 Conectando ao Supabase remoto...")
        conn = psycopg2.connect(DB_URL)
        
        file_path = os.path.join("scripts", "migration_v50.1_sre_dlq.sql")
        print(f"📄 Aplicando arquivo: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print("✅ Tabela fila_dlq criada com sucesso no Supabase!")
            
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao aplicar migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
