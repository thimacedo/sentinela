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

    def describe(self) -> str:
        return "Instagram Scraper via Zyte API"

    async def setup(self) -> None:
        self.logger.info("Motor Zyte configurado.")

    async def teardown(self) -> None:
        self.logger.info("Motor Zyte encerrado.")

    def claim_next_target(self) -> Optional[Target]:
        # 1. Alvo manual
        manual_target = self.config.get("target") or os.getenv("TEST_TARGET_USERNAME")
        if manual_target:
            return Target(username=manual_target.strip().lstrip("@"), source="manual_test")

        # 2. Fila Coleta (Apenas leitura)
        pending = self.db.table("fila_coleta").select("*").eq("status", "PENDENTE").limit(1).execute()
        if pending.data:
            item = pending.data[0]
            username = item["candidato_id"]
            
            # Não fazemos update no status da fila para evitar erro de constraint.
            # Em vez disso, marcamos o candidato como processado.
            self.db.table("candidatos").update({"last_scraped_at": datetime.now(timezone.utc).isoformat()}).eq("username", username).execute()
            
            return Target(
                username=username, 
                candidato_id=username, 
                queue_id=item["id"], 
                source="fila_coleta"
            )

        # 3. Fallback: Candidatos Ativos
        candidatos = self.db.table("candidatos").select("id,username").eq("status_monitoramento", "Ativo").limit(5).execute()
        for cand in candidatos.data or []:
            return Target(username=cand["username"], candidato_id=cand["id"], source="candidatos_fallback")
        
        return None

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        target = self.claim_next_target()
        
        if not target:
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="target_claim",
                simulated=False,
                error="no_target_available"
            )

        self.logger.info(f"Alvo selecionado: @{target.username} | origem={target.source}")
        
        # Simulação de scraping real
        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            target=target.username,
            target_id=target.candidato_id,
            source=target.source,
            simulated=True,
            error="zyte_fetch_not_implemented"
        )
