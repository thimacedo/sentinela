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

    async def setup(self) -> None:
        """Inicializacao de recursos (obrigatorio BaseWorker)."""
        self.logger.info(f"[Curador] {self.worker_id} pronto.")

    async def teardown(self) -> None:
        """Liberacao de recursos (obrigatorio BaseWorker)."""
        self.logger.info(f"[Curador] {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        target_username = None
        extracted = 0
        error = None
        quality_score = 0.0
        
        try:
            # 1. PRIORIDADE 1: Busca alvos pendentes de validação CRÍTICA
            res = db_client.client.table('candidatos')\
                .select('username')\
                .filter('status_monitoramento', 'ilike', 'Ativo')\
                .is_('identidade_validada', 'null')\
                .order('nota_relevancia', desc=True)\
                .limit(1)\
                .execute()

            # 2. TAREFA DE UTILIDADE (PASA v85.12): Enriquecimento de Dados Faltantes
            if not res.data:
                self.logger.info(f"[Curador] Fila de validação vazia. Iniciando Enriquecimento de Metadados...")
                res = db_client.client.table('candidatos')\
                    .select('username')\
                    .filter('status_monitoramento', 'ilike', 'Ativo')\
                    .or_('bio.is.null,seguidores.eq.0')\
                    .order('atualizado_em', desc=False)\
                    .limit(1)\
                    .execute()

            if res.data:
                target_username = res.data[0]['username']
                self.logger.info(f"[Curador] Processando (Utilidade/Validação): @{target_username}")
                
                # Executa inteligência via serviço unificado
                data = await intelligence_service.research_and_validate(target_username)
                
                if data:
                    extracted = 1
                    quality_score = data.get("_quality", 0.5)
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
