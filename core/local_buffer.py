import sqlite3
import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid

logger = logging.getLogger("core.local_buffer")

# Detecta ambiente cloud (filesystem efêmero)
_IS_CLOUD = bool(
    os.getenv("GITHUB_ACTIONS") or
    os.getenv("RENDER") or
    os.getenv("RAILWAY_ENVIRONMENT")
)


class LocalBuffer:
    """
    Gerencia o armazenamento local de emergência (PASA v80.0).
    - Ambiente local: SQLite persistente (Zero-Loss Policy)
    - Ambiente cloud (GitHub Actions/Render): buffer em memória
      sincronizado diretamente ao Supabase em cada inserção.
    """
    def __init__(self, db_path: str = "runtime_state/buffer.db"):
        self.is_cloud = _IS_CLOUD
        self._sqlite_has_trace_id = True
        if self.is_cloud:
            logger.info("☁️ [Buffer] Ambiente cloud detectado. Usando buffer em memória (sem SQLite).")
            self._memory_buffer: List[Dict[str, Any]] = []
        else:
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
                    trace_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(id_externo, candidato_id, post_shortcode)
                )
            """)
            cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_comments)").fetchall()}
            if "trace_id" not in cols:
                conn.execute("ALTER TABLE pending_comments ADD COLUMN trace_id TEXT")
                cols = {row[1] for row in conn.execute("PRAGMA table_info(pending_comments)").fetchall()}
            self._sqlite_has_trace_id = "trace_id" in cols
            conn.commit()

    def save(self, comments: List[Dict[str, Any]]):
        """Salva uma lista de comentários no buffer local com Trace ID."""
        for c in comments:
            if not c.get("trace_id"):
                c["trace_id"] = str(uuid.uuid4())
                
        if self.is_cloud:
            self._memory_buffer.extend(comments)
            logger.debug(f"💾 [Buffer] {len(comments)} registros no buffer em memória (cloud).")
            return

        inserted = 0
        with sqlite3.connect(self.db_path) as conn:
            for c in comments:
                try:
                    if self._sqlite_has_trace_id:
                        conn.execute(
                            "INSERT INTO pending_comments (id_externo, candidato_id, post_shortcode, data_json, trace_id) VALUES (?, ?, ?, ?, ?)",
                            (c.get("id_externo"), c.get("candidato_id"), c.get("post_shortcode"), json.dumps(c, ensure_ascii=False), c.get("trace_id"))
                        )
                    else:
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
        if self.is_cloud:
            return [{"buffer_id": i, **c} for i, c in enumerate(self._memory_buffer[:limit])]
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if self._sqlite_has_trace_id:
                cursor = conn.execute("SELECT id, data_json, trace_id FROM pending_comments ORDER BY created_at ASC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT id, data_json FROM pending_comments ORDER BY created_at ASC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                data = json.loads(row["data_json"])
                trace_id = row["trace_id"] if self._sqlite_has_trace_id else None
                if trace_id and "trace_id" not in data:
                    data["trace_id"] = trace_id
                result.append({"buffer_id": row["id"], **data})
            return result

    def delete_many(self, ids: List[int]):
        """Remove registros do buffer após sucesso no upload."""
        if self.is_cloud:
            # Em cloud, limpa os primeiros N itens do buffer de memória
            count = len(ids)
            if count <= len(self._memory_buffer):
                self._memory_buffer = self._memory_buffer[count:]
            return
        if not ids: return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"DELETE FROM pending_comments WHERE id IN ({','.join(['?']*len(ids))})", ids)
            conn.commit()
        logger.debug(f"🧹 [Buffer] {len(ids)} registros removidos do buffer local.")

    def get_count(self) -> int:
        if self.is_cloud:
            return len(self._memory_buffer)
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM pending_comments").fetchone()[0]

    async def sync_with_supabase(self, db_client: Any):
        """Tenta sincronizar o buffer local com o banco remoto (PASA v65.2)."""
        pending = self.get_pending(limit=500)
        if not pending: return 0
        
        from core.ai_service import clean_null_chars
        clean_pending = []
        ids_to_delete = []
        for p in pending:
            ids_to_delete.append(p.pop("buffer_id"))
            clean_pending.append(p)

        try:
            res = db_client.table("comentarios").upsert(
                clean_null_chars(clean_pending), 
                on_conflict="candidato_id,post_shortcode,id_externo", 
                ignore_duplicates=True
            ).execute()
            
            # Sucesso na execução -> Remove do buffer (mesmo que sejam duplicatas ignoradas)
            self.delete_many(ids_to_delete)
            return len(ids_to_delete)
            
        except Exception as e:
            error_msg = str(e)
            if "analise_pericial" in error_msg or "trace_id" in error_msg or "PGRST204" in error_msg:
                logger.warning("⚠️ [Buffer] Schema mismatch detectado no sync. Tentando fallback sem colunas opcionais...")
                try:
                    fallback_pending = []
                    for p in clean_pending:
                        p.pop("analise_pericial", None)
                        p.pop("trace_id", None)
                        fallback_pending.append(p)
                    
                    res = db_client.table("comentarios").upsert(
                        clean_null_chars(fallback_pending),
                        on_conflict="candidato_id,post_shortcode,id_externo",
                        ignore_duplicates=True
                    ).execute()
                    
                    self.delete_many(ids_to_delete)
                    return len(ids_to_delete)
                except Exception as e2:
                    logger.error(f"❌ [Buffer] Falha total no sync (mesmo com fallback): {e2}")
            else:
                logger.error(f"❌ [Buffer] Erro na sincronização: {e}")
        return 0

local_buffer = LocalBuffer()
