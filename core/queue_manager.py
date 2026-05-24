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
        Retorna o próximo alvo disponível com base em prioridades e distribuição (v55.1).
        Prioridades: Manual > fila_coleta (High Priority) > fila_coleta (Normal) > Fallback Rotation.
        """
        blocked = seen_targets | (active_targets or set())

        # 1. PRIORIDADE MÁXIMA: Alvo Manual
        manual_target = config.get("target") or os.getenv("TEST_TARGET_USERNAME")
        if manual_target:
            username = manual_target.strip().lstrip("@")
            if username not in blocked:
                logger.info(f"📍 [Queue] Selecionado alvo manual: @{username}")
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(username=username, candidato_id=username, source="manual")

        # 2. DISTRIBUIÇÃO PONDERADA: fila_coleta vs Fallback
        # Mecanismo de Fairness: 25% de chance de priorizar a rotação global para evitar estagnação.
        import random
        prefer_global_rotation = random.random() < 0.25
        
        target = None
        if not prefer_global_rotation:
            target = self._get_from_fila_coleta(blocked, seen_queue_ids, seen_targets, active_targets)
        
        if not target:
            target = self._get_from_global_rotation(blocked, seen_targets, active_targets)
            
        return target

    def _get_from_fila_coleta(self, blocked, seen_queue_ids, seen_targets, active_targets) -> Optional[Target]:
        """Busca alvos na fila de prioridade, ordenados por nível de importância."""
        try:
            # Pega os Top 20 pendentes (Alta prioridade primeiro, depois FIFO)
            pending = self.db.table("fila_coleta")\
                .select("*")\
                .eq("status", "PENDENTE")\
                .order("prioridade", desc=True)\
                .order("created_at", desc=False)\
                .limit(20).execute()
            
            for item in pending.data or []:
                queue_id = item["id"]
                username = item.get("username") or item.get("candidato_id") or item.get("target_username")
                
                # Resolução de ID para Username se necessário
                if username and len(str(username)) > 30:
                    cand = self.db.table("candidatos").select("username").eq("id", username).limit(1).execute()
                    if cand.data: username = cand.data[0]["username"]
                
                username = str(username).strip().lstrip("@")
                
                if queue_id in seen_queue_ids or username in blocked:
                    continue
                
                logger.info(f"⚡ [Queue] Selecionado da Fila de Prioridade (P{item.get('prioridade', 1)}): @{username}")
                seen_queue_ids.add(queue_id)
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(
                    username=username,
                    candidato_id=username,
                    queue_id=queue_id,
                    source="fila_coleta",
                )
        except Exception as e:
            logger.error(f"❌ [Queue] Erro ao consultar fila_coleta: {e}")
        return None

    def _get_from_global_rotation(self, blocked, seen_targets, active_targets) -> Optional[Target]:
        """Garante que todos os candidatos ativos sejam processados circularmente."""
        try:
            candidatos = self.db.table("candidatos")\
                .select("id,username")\
                .eq("status_monitoramento", "Ativo")\
                .order("last_scraped_at", desc=False)\
                .limit(15).execute()
                
            for cand in candidatos.data or []:
                username = cand["username"]
                if username in blocked:
                    continue
                
                logger.info(f"🔄 [Queue] Selecionado via Rotação Global: @{username}")
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(
                    username=username,
                    candidato_id=username,
                    source="candidatos_fallback",
                )
        except Exception as e:
            logger.error(f"❌ [Queue] Erro ao consultar rotação global: {e}")
        return None

    def _add_to_blocked(self, username, seen_targets, active_targets):
        """Marca o alvo como em processamento para evitar colisão entre workers."""
        seen_targets.add(username)
        if active_targets is not None:
            active_targets.add(username)

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