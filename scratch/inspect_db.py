import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL não configurada no .env")
        return
        
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # 1. Listar políticas de RLS da tabela comentarios
    cur.execute("""
        SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check 
        FROM pg_policies 
        WHERE tablename = 'comentarios';
    """)
    policies = cur.fetchall()
    print("=== POLÍTICAS RLS (comentarios) ===")
    for p in policies:
        print(f"Policy: {p[2]} | Roles: {p[3]} | Cmd: {p[4]} | Qual: {p[5]}")
        
    # 2. Verificar se RLS está ativo
    cur.execute("""
        SELECT relname, relrowsecurity, relforcerowsecurity 
        FROM pg_class 
        WHERE relname = 'comentarios';
    """)
    rls_status = cur.fetchone()
    print("\n=== STATUS RLS (comentarios) ===")
    print(f"Table: {rls_status[0]} | Row Security Enabled: {rls_status[1]} | Force RLS: {rls_status[2]}")
    
    # 3. Listar colunas da tabela comentarios
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'comentarios';
    """)
    columns = cur.fetchall()
    print("\n=== COLUNAS (comentarios) ===")
    for col in columns:
        print(f"Col: {col[0]} ({col[1]}) | Nullable: {col[2]}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
