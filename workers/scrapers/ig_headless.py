from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service, clean_null_chars
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
        self.seen_targets.clear()
        self.seen_queue_ids.clear()

        target = self.queue.claim_next_target(
            self.config, self.seen_queue_ids, self.seen_targets,
            active_targets=getattr(self, "active_targets", None),
        )
        if not target:
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="target_claim", simulated=False, error="no_target_available"
            )

        self.logger.info("[Headless] Ciclo %s | Alvo: @%s", self.cycle, target.username)
        
        # Atualiza last_scraped_at preventivamente
        self.queue.mark_candidate_scraped(target)

        extracted = 0
        inserted = 0
        classified = 0
        failed = 0
        db_success = False
        error_msg = None

        try:
            max_posts = self.config.get("max_posts")
            # O scraper ja realiza a persistencia interna agora
            comments = await self._scraper.run(targets=[{"username": target.username}], max_posts=max_posts)
            extracted = len(comments)

            if comments:
                db_success = True
                # Busca IDs dos comentarios recem inseridos para classificar
                # Nota: O ideal seria o scraper retornar os IDs, mas por agora buscamos no DB
                try:
                    res = self.db.table("comentarios")\
                        .select("id, texto_bruto")\
                        .eq("candidato_id", target.username)\
                        .eq("processado_ia", False)\
                        .order("data_coleta", desc=True)\
                        .limit(extracted)\
                        .execute()
                    
                    to_classify = res.data or []
                    inserted = len(to_classify) # Aproximacao

                    for item in to_classify:
                        try:
                            result = await ai_service.classify_text(item["texto_bruto"])
                            self.db.table("comentarios").update({
                                "processado_ia": True,
                                "is_hate": result["is_hate"],
                                "categoria_ia": result["categoria_ia"],
                                "confianca_ia": result["confianca_ia"],
                                "evidence_extracted": result["evidencia_lexical"],
                            }).eq("id", item["id"]).execute()
                            classified += 1
                        except Exception as e:
                            self.logger.error("[Headless] Falha ao classificar %s: %s", item["id"], e)
                            failed += 1
                except Exception as e:
                    self.logger.error("[Headless] Erro ao buscar comentarios para classificacao: %s", e)
            else:
                error_msg = "no_comments_found"

        except Exception as exc:
            self.logger.error("[Headless] Erro critico no ciclo: %s", exc)
            failed = 1
            error_msg = str(exc)[:200]

        finally:
            self.queue.rotate_target(target)

        return CycleResult(
            worker_id=self.worker_id, cycle=self.cycle,
            target=target.username, target_id=target.candidato_id,
            source="headless",
            extracted=extracted,
            inserted=inserted,
            duplicated=extracted - inserted if extracted > inserted else 0,
            classified=classified,
            failed=failed,
            db_success=db_success,
            classifier_success=classified > 0,
            simulated=False,
            error=error_msg,
        )
