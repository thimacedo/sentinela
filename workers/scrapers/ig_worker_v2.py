from __future__ import annotations

import logging
import asyncio
from typing import List, Dict

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service, clean_null_chars
from core.instagram_scraper_v2 import InstagramScraperV2

logger = logging.getLogger("worker.ig_v2")

class IGWorkerV2(BaseWorker):
    """
    Worker Instagram V2 (Independente).
    Implementa o fluxo completo de coleta e classificação usando o motor V2.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self.scraper = InstagramScraperV2(
            headless=config.get("headless", True),
            max_retries=config.get("max_retries", 3)
        )

    def describe(self) -> str:
        return "Instagram Scraper V2 - Independente com Playwright"

    async def setup(self) -> None:
        logger.info(f"🚀 Worker {self.worker_id} configurado.")

    async def teardown(self) -> None:
        logger.info(f"🛑 Worker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        self.seen_targets.clear()
        self.seen_queue_ids.clear()

        target = self.queue.claim_next_target(
            self.config, self.seen_queue_ids, self.seen_targets,
            active_targets=getattr(self, "active_targets", None),
        )

        if not target:
            # Backlog de classificação se não houver alvo
            classified = await ai_service.run_batch_classification(limit=50)
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="batch_classification", simulated=False, error="no_target",
                classified=classified
            )

        self.logger.info(f"🔄 [V2] Ciclo {self.cycle} | Alvo: @{target.username}")
        
        # Jitter inicial (PASA v52.0) para quebrar padrões
        import random
        jitter = random.uniform(5, 30)
        self.logger.debug(f"[V2] Aplicando jitter inicial de {jitter:.1f}s")
        await asyncio.sleep(jitter)

        self.queue.mark_candidate_scraped(target)

        try:
            # 1. Scraping
            comments = await self.scraper.scrape_profile(
                username=target.username,
                candidato_id=target.candidato_id,
                max_posts=self.config.get("max_posts", 3),
                max_comments_per_post=100
            )
        except ValueError as e:
            if "invalid_target" in str(e):
                self.logger.error(f"🚫 [V2] Alvo @{target.username} marcado como INVÁLIDO (404/Privado/Mismatch).")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, 
                    error=str(e), db_success=False # db_success=False garante score baixo
                )
            raise e

        try:
            stats = self.scraper.get_stats()

            if not comments:
                if stats.get("junk_detected", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Apenas lixo detectado para @{target.username}. Sinalizando falha de extração.")
                    return CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, simulated=False, error="junk_detected"
                    )
                # Se o scraper retornou vazio mas não levantou erro, pode ser apenas falta de conteúdo
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, error="no_comments_found"
                )

            # 2. Persistência
            inserted = 0
            duplicated = 0
            inserted_ids = []
            
            try:
                # Upsert em lote
                res = self.db.table("comentarios").upsert(
                    clean_null_chars(comments), 
                    on_conflict="candidato_id,post_shortcode,id_externo",
                    ignore_duplicates=True
                ).execute()
                
                inserted = len(res.data)
                duplicated = len(comments) - inserted
                inserted_ids = [str(item["id"]) for item in res.data]
            except Exception as e:
                self.logger.error(f"❌ Erro na persistência: {e}")

            # 3. Classificação
            classified = 0
            ai_junk_count = 0
            
            if inserted_ids:
                for cid in inserted_ids:
                    try:
                        # Busca comentário e classifica
                        c_data = self.db.table("comentarios").select("texto_bruto").eq("id", cid).single().execute()
                        if c_data.data:
                            result = await ai_service.classify_text(c_data.data["texto_bruto"], comment_id=cid)
                            
                            if result.get("categoria_ia") == "LIXO":
                                # Lixo detectado pela IA pós-inserção
                                self.db.table("comentarios").delete().eq("id", cid).execute()
                                inserted -= 1
                                ai_junk_count += 1
                                # Remove também dos extraídos para não premiar na coleta
                                comments = [c for c in comments if c.get("id_externo") != cid] # Tenta manter sync, mas o len(comments) inicial já foi feito. Vamos apenas decrementar uma variável.
                                continue
                                
                            self.db.table("comentarios").update({
                                "processado_ia": True,
                                "is_hate": result["is_hate"],
                                "categoria_ia": result["categoria_ia"],
                                "confianca_ia": result["confianca_ia"],
                                "evidence_extracted": result["evidencia_lexical"]
                            }).eq("id", cid).execute()
                            classified += 1
                    except: continue

            stats = self.scraper.get_stats()
            final_extracted = len(comments) - ai_junk_count
            
            if final_extracted <= 0 and (stats.get("junk_detected", 0) > 0 or ai_junk_count > 0):
                self.logger.warning(f"⚠️ [V2] Todo o conteúdo extraído de @{target.username} era LIXO. Sinalizando falha e anulando recompensas.")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, inserted=0, classified=0, simulated=False, error="junk_detected"
                )

            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="v2_engine",
                extracted=final_extracted,
                inserted=inserted,
                duplicated=duplicated,
                classified=classified,
                db_success=inserted > 0,
                classifier_success=classified > 0,
                simulated=False
            )

        except Exception as e:
            self.logger.error(f"💥 Erro crítico no ciclo V2: {e}")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                failed=1, error=str(e)[:200], simulated=False
            )
        finally:
            self.queue.rotate_target(target)
