from __future__ import annotations
import asyncio
import logging
from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.intelligence_service import intelligence_service
from core.db import db_client

logger = logging.getLogger("worker.researcher")

class TargetResearchWorker(BaseWorker):
    """
    Worker especializado em curadoria e manutenção de dados de alvos (PASA v84.16).
    Utiliza IntelligenceService para processamento estruturado.
    Saneado para compatibilidade com terminais Windows.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0

    def describe(self) -> str:
        return "Motor de Curadoria e Inteligencia de Alvos"

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        target_username = None
        extracted = 0
        error = None
        quality_score = 0.0
        
        try:
            # 1. Busca alvos pendentes de validacao ou curadoria
            res = db_client.client.table('candidatos')\
                .select('username')\
                .or_('identidade_validada.is.null,cargo.eq.DESCONHECIDO,cargo.is.null')\
                .eq('status_monitoramento', 'ATIVO')\
                .order('atualizado_em', desc=False)\
                .limit(1)\
                .execute()

            if res.data:
                target_username = res.data[0]['username']
                self.logger.info(f"[Curador] Processando: @{target_username}")
                
                # Executa inteligencia via servico unificado
                data = await intelligence_service.research_and_validate(target_username)
                
                if data:
                    extracted = 1
                    quality_score = data.get("_quality", 0.5)
                    if data.get("status_monitoramento") == "DESATIVADO":
                        self.logger.warning(f"[Curador] @{target_username} desativado.")
            else:
                error = "no_tasks_available"

        except Exception as e:
            self.logger.error(f"Erro na curadoria: {e}")
            error = str(e)

        # Calculo de Recompensas simplificado
        xp_delta = 15.0 if quality_score > 0.8 else (5.0 if extracted > 0 else -5.0)
        if error == "no_tasks_available": xp_delta = 0.0

        return CycleResult(
            worker_id=self.worker_id, cycle=self.cycle, target=target_username,
            source="intelligence_curation", extracted=extracted,
            db_success=extracted > 0, classifier_success=extracted > 0,
            duration=asyncio.get_event_loop().time() - start_time,
            error=error, metadata={"xp_delta": xp_delta, "quality": quality_score}
        )
