from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service
from core.instagram_headless import InstagramHeadlessScraper
import logging

class IGHeadlessWorker(BaseWorker):
    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.logger = logging.getLogger(f"worker.{worker_id}")
        self.cycle = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self._scraper = InstagramHeadlessScraper()

    def describe(self) -> str:
        return "Instagram Scraper via Playwright Headless (Tier 2)"

    async def setup(self) -> None:
        self.logger.info("Motor Headless configurado.")

    async def teardown(self) -> None:
        self.logger.info("Motor Headless encerrado.")

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        # Limpa seen_targets a cada ciclo para permitir re-visita de alvos
        self.seen_targets.clear()
        self.seen_queue_ids.clear()

        target = self.queue.claim_next_target(self.config, self.seen_queue_ids, self.seen_targets)
        if not target:
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="target_claim", simulated=False, error="no_target_available"
            )

        self.logger.info("🎯 [Headless] Ciclo %s | Alvo: @%s", self.cycle, target.username)

        try:
            comments = await self._scraper.run(targets=[{"username": target.username}])
            if not comments:
                self.queue.rotate_target(target)
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle,
                    target=target.username, target_id=target.candidato_id,
                    source="headless", extracted=0, simulated=False,
                    error="no_comments_found"
                )

            # Persistência
            inserted = 0
            failed = 0
            inserted_ids = []
            try:
                res = self.db.table("comentarios").upsert(
                    comments, on_conflict="id_externo", ignore_duplicates=True
                ).execute()
                inserted = len(res.data)
                inserted_ids = [str(item["id"]) for item in res.data]
            except Exception as e:
                self.logger.error("❌ [Headless] Falha na persistência: %s", e)
                failed = len(comments)

            # Classificação
            classified = 0
            for comment_id in inserted_ids:
                try:
                    res = self.db.table("comentarios").select("texto_bruto").eq("id", comment_id).single().execute()
                    if not res.data:
                        continue
                    result = await ai_service.classify_text(res.data["texto_bruto"])
                    self.db.table("comentarios").update({
                        "processado_ia": True,
                        "is_hate": result["is_hate"],
                        "categoria_ia": result["categoria_ia"],
                        "confianca_ia": result["confianca_ia"],
                        "evidence_extracted": result["evidencia_lexical"],
                    }).eq("id", comment_id).execute()
                    classified += 1
                except Exception as e:
                    self.logger.error("❌ [Headless] Falha ao classificar %s: %s", comment_id, e)

            if inserted > 0:
                self.queue.mark_candidate_scraped(target)
            self.queue.rotate_target(target)

            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target=target.username, target_id=target.candidato_id,
                source="headless",
                extracted=len(comments),
                inserted=inserted,
                duplicated=len(comments) - inserted - failed,
                classified=classified,
                failed=failed,
                db_success=inserted > 0,
                classifier_success=classified > 0,
                simulated=False,
            )

        except Exception as exc:
            self.logger.error("💥 [Headless] Erro crítico no ciclo: %s", exc)
            self.queue.rotate_target(target)
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target=target.username, target_id=target.candidato_id,
                source="headless", failed=1, error=str(exc)[:200], simulated=False
            )
