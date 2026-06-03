# workers/analytics/report_worker.py
from __future__ import annotations
import asyncio
import sys
from datetime import datetime, UTC
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from workers.core.base_worker import BaseWorker
from core.supabase_service import get_supabase_client
from workers.analytics.trends_worker import generate_trends
from workers.analytics.network_worker import generate_network


class ReportWorker(BaseWorker):
    def __init__(self):
        # max_retries=1: relatórios não devem rodar duas vezes por acidente
        super().__init__(name="ReportWorker", max_retries=1)
        self.db = get_supabase_client()

    async def _run(self, payload: dict) -> list:
        self.logger.info("📊 Iniciando auditoria e calibração de recompensas...")

        candidatos = self.db.table("candidatos") \
            .select("id, username, prioridade_coleta, last_scraped_at") \
            .execute().data or []

        comentarios = self.db.table("comentarios") \
            .select("candidato_id, is_hate") \
            .execute().data or []

        stats: dict[str, dict] = {}
        for c in comentarios:
            cid = c["candidato_id"]
            if not cid:
                continue
            stats.setdefault(cid, {"total": 0, "hate": 0})
            stats[cid]["total"] += 1
            if c["is_hate"]:
                stats[cid]["hate"] += 1

        relatorio = []
        ajustes = 0

        for cand in candidatos:
            username = cand["username"]
            last_scrape = cand.get("last_scraped_at")
            current_prio = cand.get("prioridade_coleta", 1)
            s = stats.get(username, {"total": 0, "hate": 0})

            if not last_scrape:
                new_prio = current_prio
                status = "🔴 PENDENTE"
            else:
                score = s["total"] + s["hate"] * 5
                if score > 50:
                    new_prio, status = 5, "🟣 ALTO VALOR"
                elif score > 20:
                    new_prio, status = 4, "🟢 COBERTO"
                elif score > 5:
                    new_prio, status = 3, "🟢 COBERTO"
                elif s["total"] > 0:
                    new_prio, status = 2, "🟡 BAIXO VALOR"
                else:
                    new_prio, status = 1, "⚫ ZONA MORTA"

                if new_prio != current_prio:
                    self.db.table("candidatos") \
                        .update({"prioridade_coleta": new_prio}) \
                        .eq("id", cand["id"]).execute()
                    ajustes += 1

            relatorio.append({
                "candidato": f"@{username}",
                "status": status,
                "prio_nova": new_prio,
                "comentarios": s["total"],
                "hate": s["hate"],
            })

        self.logger.info(
            f"✅ Relatório gerado | {len(relatorio)} candidatos "
            f"| {ajustes} ajustes de prioridade"
        )
        trend_path = generate_trends()
        network_path = generate_network()
        self.logger.info(f"✅ Trends generated at {trend_path}")
        self.logger.info(f"✅ Network generated at {network_path}")
        return relatorio  # BaseWorker usa len() para registrar items_processed



if __name__ == "__main__":
    asyncio.run(ReportWorker().execute({}))
