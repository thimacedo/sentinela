from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from dataclasses import dataclass
from typing import Optional
from core.supabase_service import get_supabase_client
import logging
import os
from datetime import datetime, timezone

@dataclass
class Target:
    username: str
    candidato_id: Optional[str] = None
    queue_id: Optional[str] = None
    source: str = "unknown"

class IGZyteWorker(BaseWorker):
    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.logger = logging.getLogger(f"worker.{worker_id}")
        self.cycle = 0
        self.db = get_supabase_client()
        self.seen_queue_ids = set()
        self.seen_targets = set()

    def describe(self) -> str:
        return "Instagram Scraper via Zyte API"

    async def setup(self) -> None:
        self.logger.info("Motor Zyte configurado.")

    async def teardown(self) -> None:
        self.logger.info("Motor Zyte encerrado.")

    def rotate_target(self, target: Target):
        if not target.queue_id: return
        
        # 1. Remove da frente
        self.db.table("fila_coleta").delete().eq("id", target.queue_id).execute()
        
        # 2. Re-insere no fim
        self.db.table("fila_coleta").insert({
            "candidato_id": target.candidato_id,
            "status": "PENDENTE",
            "prioridade": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()

    def claim_next_target(self) -> Optional[Target]:
        # 1. Alvo manual
        manual_target = self.config.get("target") or os.getenv("TEST_TARGET_USERNAME")
        if manual_target:
            username = manual_target.strip().lstrip("@")
            if username in self.seen_targets: return None
            self.seen_targets.add(username)
            return Target(username=username, source="manual_test")

        # 2. Fila Coleta
        pending = self.db.table("fila_coleta").select("*").eq("status", "PENDENTE").limit(20).execute()
        for item in pending.data or []:
            queue_id = item["id"]
            username = item.get("username") or item.get("candidato_id") or item.get("target_username")
            
            if username and len(str(username)) > 30:
                cand = self.db.table("candidatos").select("username").eq("id", username).limit(1).execute()
                if cand.data: username = cand.data[0]["username"]
            
            username = str(username).strip().lstrip("@")
            
            if queue_id in self.seen_queue_ids or username in self.seen_targets:
                continue
            
            self.seen_queue_ids.add(queue_id)
            self.seen_targets.add(username)
            
            return Target(
                username=username, 
                candidato_id=username, 
                queue_id=queue_id, 
                source="fila_coleta"
            )

        # 3. Fallback: Candidatos Ativos
        candidatos = self.db.table("candidatos").select("id,username").eq("status_monitoramento", "Ativo").order("last_scraped_at", desc=False).limit(10).execute()
        for cand in candidatos.data or []:
            username = cand["username"]
            if username in self.seen_targets: continue
            self.seen_targets.add(username)
            return Target(username=username, candidato_id=cand["id"], source="candidatos_fallback")
        
        return None

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        target = self.claim_next_target()
        
        if not target:
            if self.cycle == 1:
                self.logger.warning("Nenhum alvo disponível para coleta.")
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="target_claim",
                simulated=False,
                error="no_target_available"
            )

        self.logger.info(f"Alvo selecionado: @{target.username} | origem={target.source}")
        
        result = CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            target=target.username,
            target_id=target.candidato_id,
            source=target.source,
            simulated=True,
            error="zyte_fetch_not_implemented"
        )
        
        if target.source == "fila_coleta":
            self.rotate_target(target)
            
        return result
