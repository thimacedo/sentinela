from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from models.target import Target

logger = logging.getLogger("queue_manager")


class QueueManager:
    def __init__(self, db_client):
        self.db = db_client

    def claim_next_target(
        self,
        config: dict,
        seen_queue_ids: set,
        seen_targets: set,
        active_targets: Optional[set] = None,
    ) -> Optional[Target]:
        """
        Retorna o proximo alvo disponivel.
        active_targets: set compartilhado entre workers para evitar alvos duplicados no mesmo ciclo.
        """
        # Unifica seen_targets com active_targets para o check
        blocked = seen_targets | (active_targets or set())

        # Manual target from config or env
        manual_target = config.get("target") or os.getenv("TEST_TARGET_USERNAME")
        if manual_target:
            username = manual_target.strip().lstrip("@")
            if username in blocked:
                return None
            seen_targets.add(username)
            if active_targets is not None:
                active_targets.add(username)
            return Target(username=username, source="manual_test")

        # Pending fila (Priority Queue)
        # Adicionado ordering por created_at para garantir FIFO e rotação real.
        # Adicionado mecanismo de fairness: 20% de chance de pular a fila de prioridade 
        # para garantir que a rotação global de candidatos não estacione.
        import random
        use_priority_queue = random.random() > 0.2
        
        if use_priority_queue:
            pending = self.db.table("fila_coleta")\
                .select("*")\
                .eq("status", "PENDENTE")\
                .order("prioridade", desc=True)\
                .order("created_at", desc=False)\
                .limit(20).execute()
            
            for item in pending.data or []:
                queue_id = item["id"]
                username = item.get("username") or item.get("candidato_id") or item.get("target_username")
                if username and len(str(username)) > 30:
                    cand = self.db.table("candidatos").select("username").eq("id", username).limit(1).execute()
                    if cand.data:
                        username = cand.data[0]["username"]
                username = str(username).strip().lstrip("@")
                if queue_id in seen_queue_ids or username in blocked:
                    continue
                seen_queue_ids.add(queue_id)
                seen_targets.add(username)
                if active_targets is not None:
                    active_targets.add(username)
                return Target(
                    username=username,
                    candidato_id=username,
                    queue_id=queue_id,
                    source="fila_coleta",
                )

        # Fallback to candidatos (Global Rotation)
        candidatos = self.db.table("candidatos")\
            .select("id,username")\
            .eq("status_monitoramento", "Ativo")\
            .order("last_scraped_at", desc=False)\
            .limit(10).execute()
        for cand in candidatos.data or []:
            username = cand["username"]
            if username in blocked:
                continue
            seen_targets.add(username)
            if active_targets is not None:
                active_targets.add(username)
            return Target(
                username=username,
                candidato_id=username, # Foreign key mapeia para username
                source="candidatos_fallback",
            )
        return None

    def rotate_target(self, target: Target) -> None:
        """Remove o item processado e reinsere no fim da fila (idempotente)."""
        if not target.queue_id:
            return
        self.db.table("fila_coleta").delete().eq("id", target.queue_id).execute()
        try:
            self.db.table("fila_coleta").upsert(
                {
                    "candidato_id": target.candidato_id,
                    "status": "PENDENTE",
                    "prioridade": 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                on_conflict="candidato_id,data_agendada",
                ignore_duplicates=True,
            ).execute()
        except Exception as e:
            code = getattr(e, "code", None) or ""
            if "23505" in str(code) or "23505" in str(e):
                logger.warning("[QueueManager] rotate_target: duplicata ignorada para %s", target.candidato_id)
            else:
                logger.error("[QueueManager] rotate_target falhou: %s", e)

    def mark_candidate_scraped(self, target: Target) -> None:
        """Update the last_scraped_at timestamp for the candidate."""
        if not target.username:
            return
        self.db.table("candidatos").update({
            "last_scraped_at": datetime.now(timezone.utc).isoformat(),
        }).eq("username", target.username).execute()