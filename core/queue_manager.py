from typing import Optional, List, Dict, Any
from models.target import Target
import os
from datetime import datetime, timezone

class QueueManager:
    def __init__(self, db_client):
        """
        db_client: Supabase client from core.supabase_service.get_supabase_client()
        """
        self.db = db_client

    def claim_next_target(
        self,
        config: dict,
        seen_queue_ids: set,
        seen_targets: set,
    ) -> Optional[Target]:
        """
        Implements the same logic as the original IGZyteWorker.claim_next_target,
        but receives seen sets as parameters to avoid internal state.
        Returns a Target or None.
        """
        # Manual target from config or env
        manual_target = config.get("target") or os.getenv("TEST_TARGET_USERNAME")
        if manual_target:
            username = manual_target.strip().lstrip("@")
            if username in seen_targets:
                return None
            seen_targets.add(username)
            return Target(username=username, source="manual_test")

        # Pending fila
        pending = self.db.table("fila_coleta").select("*").eq("status", "PENDENTE").limit(20).execute()
        for item in pending.data or []:
            queue_id = item["id"]
            username = item.get("username") or item.get("candidato_id") or item.get("target_username")
            if username and len(str(username)) > 30:
                cand = self.db.table("candidatos").select("username").eq("id", username).limit(1).execute()
                if cand.data:
                    username = cand.data[0]["username"]
            username = str(username).strip().lstrip("@")
            if queue_id in seen_queue_ids or username in seen_targets:
                continue
            seen_queue_ids.add(queue_id)
            seen_targets.add(username)
            return Target(
                username=username,
                candidato_id=username,
                queue_id=queue_id,
                source="fila_coleta",
            )

        # Fallback to candidatos
        candidatos = self.db.table("candidatos").select("id,username").eq("status_monitoramento", "Ativo").order("last_scraped_at", desc=False).limit(10).execute()
        for cand in candidatos.data or []:
            username = cand["username"]
            if username in seen_targets:
                continue
            seen_targets.add(username)
            return Target(
                username=username,
                candidato_id=cand["id"],
                source="candidatos_fallback",
            )
        return None

    def rotate_target(self, target: Target) -> None:
        """Remove the processed fila entry and re-insert it at the end of the queue."""
        if not target.queue_id:
            return
        self.db.table("fila_coleta").delete().eq("id", target.queue_id).execute()
        self.db.table("fila_coleta").insert({
            "candidato_id": target.candidato_id,
            "status": "PENDENTE",
            "prioridade": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()

    def mark_candidate_scraped(self, target: Target) -> None:
        """Update the last_scraped_at timestamp for the candidate."""
        if not target.username:
            return
        self.db.table("candidatos").update({
            "last_scraped_at": datetime.now(timezone.utc).isoformat(),
        }).eq("username", target.username).execute()