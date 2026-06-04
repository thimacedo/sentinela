# scripts/export_to_sqlite.py
import os
import sys
import sqlite3
from pathlib import Path

# Ajusta o path para importar módulos da raiz
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from core.config import settings
from supabase import create_client, Client

def export_to_sqlite():
    print("[INFO] [Datasette Export] Iniciando exportacao do Supabase para SQLite local...")
    
    # 1. Verifica chaves do Supabase
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        print("[ERROR] [Datasette Export] SUPABASE_URL ou SUPABASE_KEY nao configurados nos Settings.")
        return
        
    # 2. Instancia o cliente do Supabase
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        print(f"[ERROR] [Datasette Export] Falha ao instanciar cliente do Supabase: {e}")
        return

    # 3. Garante que o diretório data/ exista
    data_dir = root_path / "data"
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "sentinela_data.db"

    # 4. Busca dados do Supabase
    print("[INFO] [Datasette Export] Buscando registros do Supabase...")
    try:
        # Puxa candidatos monitorados
        cands_resp = supabase.table("candidatos").select("*").execute()
        candidatos = cands_resp.data or []
        print(f"   -> {len(candidatos)} candidatos localizados.")
        
        # Puxa os últimos 5000 comentários para manter o SQLite rápido e otimizado localmente
        coms_resp = supabase.table("comentarios").select("*").order("data_coleta", desc=True).limit(5000).execute()
        comentarios = coms_resp.data or []
        print(f"   -> {len(comentarios)} comentarios recentes localizados.")
    except Exception as e:
        print(f"[ERROR] [Datasette Export] Erro na consulta ao Supabase: {e}")
        return

    # 5. Conecta ao banco de dados SQLite local
    print(f"[INFO] [Datasette Export] Gravando em: {db_path}")
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Cria tabela de candidatos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidatos (
                username TEXT PRIMARY KEY,
                nome_completo TEXT,
                status_monitoramento TEXT,
                termometro TEXT,
                last_scraped_at TEXT
            )
        """)
        
        # Cria tabela de comentários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comentarios (
                id TEXT PRIMARY KEY,
                autor_username TEXT,
                candidato_id TEXT,
                texto_limpo TEXT,
                categoria_ia TEXT,
                is_hate INTEGER,
                confianca_ia REAL,
                analise_pericial TEXT,
                data_coleta TEXT
            )
        """)
        
        # Insere candidatos
        for cand in candidatos:
            cursor.execute("""
                INSERT OR REPLACE INTO candidatos 
                (username, nome_completo, status_monitoramento, termometro, last_scraped_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                cand.get("username"),
                cand.get("nome_completo"),
                cand.get("status_monitoramento"),
                cand.get("termometro") or "FRIO",
                cand.get("last_scraped_at")
            ))
            
        # Insere comentários
        for c in comentarios:
            cursor.execute("""
                INSERT OR REPLACE INTO comentarios 
                (id, autor_username, candidato_id, texto_limpo, categoria_ia, is_hate, confianca_ia, analise_pericial, data_coleta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c.get("id"),
                c.get("autor_username"),
                c.get("candidato_id"),
                c.get("texto_limpo") or c.get("texto_bruto"),
                c.get("categoria_ia") or "NEUTRO",
                1 if c.get("is_hate") else 0,
                c.get("confianca_ia") or 0.0,
                c.get("analise_pericial"),
                c.get("data_coleta")
            ))
            
        # 6. Cria indexação Full-Text Search (FTS5) para busca textual em milissegundos
        # Remove a tabela virtual antiga se existir
        cursor.execute("DROP TABLE IF EXISTS comentarios_fts")
        
        # Cria a tabela FTS5
        cursor.execute("""
            CREATE VIRTUAL TABLE comentarios_fts USING fts5(
                id UNINDEXED,
                texto_limpo,
                autor_username,
                candidato_id
            )
        """)
        
        # Popula a tabela FTS5
        cursor.execute("""
            INSERT INTO comentarios_fts(id, texto_limpo, autor_username, candidato_id)
            SELECT id, texto_limpo, autor_username, candidato_id FROM comentarios
        """)
        
        conn.commit()
        conn.close()
        print(f"[SUCCESS] [Datasette Export] Exportacao concluida com sucesso. Banco SQLite pronto!")
    except Exception as e:
        print(f"[ERROR] [Datasette Export] Erro ao gravar banco SQLite local: {e}")

if __name__ == "__main__":
    export_to_sqlite()
