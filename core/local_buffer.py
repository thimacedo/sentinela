import sqlite3
import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger("core.local_buffer")

class LocalBuffer:
    """
    Gerencia o armazenamento local de emergência usando SQLite (PASA v65.0).
    Garante a política Zero-Loss: dados são deletados apenas após confirmação de upload.
    """
    def __init__(self, db_path: str = "runtime_state/buffer.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_externo TEXT,
                    candidato_id TEXT,
                    post_shortcode TEXT,
                    data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(id_externo, candidato_id, post_shortcode)
                )
            """)
            conn.commit()

    def save(self, comments: List[Dict[str, Any]]):
        """Salva uma lista de comentários no buffer local."""
        inserted = 0
        with sqlite3.connect(self.db_path) as conn:
            for c in comments:
                try:
                    conn.execute(
                        "INSERT INTO pending_comments (id_externo, candidato_id, post_shortcode, data_json) VALUES (?, ?, ?, ?)",
                        (c.get("id_externo"), c.get("candidato_id"), c.get("post_shortcode"), json.dumps(c, ensure_ascii=False))
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    continue # Já existe no buffer
            conn.commit()
        if inserted > 0:
            logger.info(f"💾 [Buffer] {inserted} registros salvos localmente (SQLite).")

    def get_pending(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera registros pendentes para tentativa de upload."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, data_json FROM pending_comments ORDER BY created_at ASC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [{"buffer_id": row["id"], **json.loads(row["data_json"])} for row in rows]

    def delete_many(self, ids: List[int]):
        """Remove registros do buffer após sucesso no upload."""
        if not ids: return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"DELETE FROM pending_comments WHERE id IN ({','.join(['?']*len(ids))})", ids)
            conn.commit()
        logger.debug(f"🧹 [Buffer] {len(ids)} registros removidos do buffer local.")

    def get_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM pending_comments").fetchone()[0]

    async def sync_with_supabase(self, db_client: Any):
        """Tenta sincronizar o buffer local com o banco remoto (PASA v65.1)."""
        pending = self.get_pending(limit=500)
        if not pending: return 0
        
        try:
            from core.ai_service import clean_null_chars
            clean_pending = []
            ids_to_delete = []
            for p in pending:
                ids_to_delete.append(p.pop("buffer_id"))
                clean_pending.append(p)
            
            res = db_client.table("comentarios").upsert(
                clean_null_chars(clean_pending), 
                on_conflict="candidato_id,post_shortcode,id_externo", 
                ignore_duplicates=True
            ).execute()
            
            if res.data:
                self.delete_many(ids_to_delete)
                return len(res.data)
        except Exception as e:
            logger.error(f"❌ [Buffer] Erro na sincronização: {e}")
        return 0

local_buffer = LocalBuffer()
