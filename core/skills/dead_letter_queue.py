# Dead Letter Queue (DLQ) Manager
# Arquivo: core/skills/dead_letter_queue.py

import os
import sqlite3
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("core.skills.dead_letter_queue")

class DeadLetterQueue:
    """
    Gerenciador da Dead Letter Queue (DLQ) para o Sentinela.
    Persiste falhas de coleta localmente (SQLite) para resiliência máxima,
    e tenta sincronizar com o Supabase remoto via REST se a tabela existir.
    """
    def __init__(self, db_path: str = "runtime_state/buffer.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_sqlite()
        
    def _init_sqlite(self):
        """Inicializa a tabela fila_dlq no SQLite local."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS fila_dlq (
                        id TEXT PRIMARY KEY,
                        original_target_id TEXT,
                        queue_id TEXT,
                        target_username TEXT NOT NULL,
                        platform TEXT NOT NULL DEFAULT 'INSTAGRAM',
                        error_type TEXT NOT NULL,
                        error_message TEXT,
                        stack_trace TEXT,
                        code_version TEXT DEFAULT 'v100.0',
                        retry_count INTEGER DEFAULT 0,
                        next_retry_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"[DLQ] Erro ao inicializar SQLite local: {e}")

    async def add_failed_target(
        self,
        target_username: str,
        error_type: str,
        error_message: str,
        stack_trace: str = "",
        original_target_id: Optional[str] = None,
        queue_id: Optional[str] = None,
        platform: str = "INSTAGRAM",
        code_version: str = "v100.0"
    ) -> str:
        """Registra um alvo falho na DLQ local e tenta enviar ao Supabase."""
        dlq_id = str(sqlite3.connect(self.db_path).execute("SELECT lower(hex(randomblob(16)))").fetchone()[0])
        # Formata UUID no padrão com hifens para conformidade
        dlq_id = f"{dlq_id[:8]}-{dlq_id[8:12]}-{dlq_id[12:16]}-{dlq_id[16:20]}-{dlq_id[20:]}"
        
        now_iso = datetime.now(timezone.utc).isoformat()
        next_retry = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        
        # 1. Salva localmente (SQLite)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO fila_dlq (
                        id, original_target_id, queue_id, target_username, platform,
                        error_type, error_message, stack_trace, code_version,
                        retry_count, next_retry_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """, (
                    dlq_id, original_target_id, queue_id, target_username, platform,
                    error_type, error_message, stack_trace, code_version, next_retry, now_iso
                ))
                conn.commit()
            logger.info(f"📥 [DLQ] Alvo @{target_username} registrado na DLQ local (SQLite). ID: {dlq_id}")
        except Exception as e_sql:
            logger.error(f"[DLQ] Erro ao salvar alvo falho no SQLite local: {e_sql}")

        # 2. Tenta sincronizar com o Supabase remoto via REST API
        try:
            from core.supabase_client import get_supabase_client
            db = get_supabase_client()
            
            payload = {
                "id": dlq_id,
                "original_target_id": original_target_id,
                "queue_id": queue_id,
                "target_username": target_username,
                "platform": platform,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "code_version": code_version,
                "retry_count": 0,
                "next_retry_at": next_retry,
                "created_at": now_iso
            }
            
            # Executa insert via Rest
            db.table("fila_dlq").insert(payload).execute()
            logger.info(f"☁️ [DLQ] Alvo @{target_username} sincronizado com a DLQ remota (Supabase).")
        except Exception as e_cloud:
            # Captura de forma resiliente se a tabela não existir ou se faltar conectividade
            err_str = str(e_cloud)
            if "PGRST205" in err_str or "Could not find the table" in err_str:
                logger.debug(f"[DLQ] Tabela fila_dlq ausente no Supabase. Mantendo apenas localmente.")
            else:
                logger.warning(f"[DLQ] Erro ao sincronizar com Supabase remoto: {e_cloud}")
                
        return dlq_id

    def get_pending_retries(self) -> List[Dict[str, Any]]:
        """Retorna itens da DLQ local que estão prontos para reprocessamento."""
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT * FROM fila_dlq 
                    WHERE next_retry_at <= ? AND retry_count < 3
                """, (now_iso,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"[DLQ] Erro ao consultar pendentes no SQLite: {e}")
            return []

    def increment_retry(self, dlq_id: str):
        """Incrementa a contagem de tentativas e define o próximo cooldown."""
        next_retry = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE fila_dlq 
                    SET retry_count = retry_count + 1, next_retry_at = ?
                    WHERE id = ?
                """, (next_retry, dlq_id))
                conn.commit()
        except Exception as e:
            logger.error(f"[DLQ] Erro ao atualizar retry count no SQLite: {e}")

    def delete_item(self, dlq_id: str):
        """Remove item da DLQ após sucesso de processamento."""
        try:
            # 1. Remove local
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM fila_dlq WHERE id = ?", (dlq_id,))
                conn.commit()
            logger.info(f"🗑️ [DLQ] Item {dlq_id} removido da DLQ local.")
            
            # 2. Tenta remover remoto
            try:
                from core.supabase_client import get_supabase_client
                db = get_supabase_client()
                db.table("fila_dlq").delete().eq("id", dlq_id).execute()
            except Exception as e_cloud:
                logger.debug(f"[DLQ] Erro ao remover da DLQ remota: {e_cloud}")
        except Exception as e:
            logger.error(f"[DLQ] Erro ao remover item da DLQ: {e}")

# Instância compartilhada
dead_letter_queue = DeadLetterQueue()
