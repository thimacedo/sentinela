from __future__ import annotations
import asyncio
import logging
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.db import db_client

logger = logging.getLogger("worker.treasurer")

class TreasurerWorker(BaseWorker):
    """
    Worker: Treasurer (Tesoureiro)
    Finalidade: Garantir a integridade financeira do ecossistema CI.
    Responsabilidades:
      1. Auditoria de Saldos (Prevenir tokens negativos).
      2. Cálculo de Burn Rate e Custo de Operação.
      3. Fechamento Financeiro Diário (Inflow/Outflow).
    PASA v86.1
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.daily_report_last_run = None

    def describe(self) -> str:
        return "Guardião da Integridade Financeira e Fluxo de CI"

    async def setup(self) -> None:
        logger.info(f"💰 TreasurerWorker {self.worker_id} inicializado.")

    async def teardown(self) -> None:
        logger.info(f"🛑 TreasurerWorker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        extracted = 0
        failed = 0
        error = None
        
        try:
            # 1. Auditoria de Integridade (Profiles com saldo inconsistente)
            anomalies = await self._audit_balances()
            if anomalies > 0:
                logger.warning(f"⚖️ [Treasurer] {anomalies} anomalias de saldo detectadas.")
            
            # 2. Monitoramento de Gateway (Stripe Connection Check)
            stripe_status = await self._check_stripe_connectivity()
            
            # 3. Processamento de Fechamento Diário
            now = datetime.now(timezone.utc)
            if not self.daily_report_last_run or self.daily_report_last_run.date() < now.date():
                await self._generate_daily_financial_report()
                self.daily_report_last_run = now
                extracted += 1
            
            # 4. Cálculo de Burn Rate Operacional (Custo de IA/Proxy)
            await self._compute_burn_rate()
            
            if extracted == 0 and anomalies == 0:
                error = "no_tasks_available"

        except Exception as e:
            logger.error(f"💥 Erro no TreasurerWorker: {e}")
            error = str(e)
            failed = 1

        return CycleResult(
            worker_id=self.worker_id, cycle=self.cycle,
            target="financial_ledger", source="treasurer",
            extracted=extracted, failed=failed,
            db_success=error is None, classifier_success=True,
            duration=asyncio.get_event_loop().time() - start_time,
            error=error,
            metadata={"stripe_online": stripe_status}
        )

    async def _check_stripe_connectivity(self) -> bool:
        """Verifica se o gateway de pagamento está respondendo corretamente (v86.5)."""
        import stripe
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        if not stripe.api_key:
            logger.info("ℹ️ [Treasurer] Stripe API Key ausente. Operando em modo Mock/Beta.")
            return False
        
        try:
            # Tenta listar o balanço básico para validar a chave
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, stripe.Balance.retrieve)

            logger.info("✅ [Treasurer] Conexão com Stripe estabelecida.")
            return True
        except Exception as e:
            logger.error(f"❌ [Treasurer] Falha na conexão Stripe: {e}")
            return False

    async def _audit_balances(self) -> int:
        """Verifica se existem perfis com saldo negativo."""
        try:
            # Governança de CI (v28.0)
            res = db_client.client.table('profiles').select('id, saldo_ci').lt('saldo_ci', 0).execute()
            negatives = res.data or []
            for n in negatives:
                logger.error(f"🚨 [Auditoria] SALDO NEGATIVO: ID {n.get('id')} ({n.get('saldo_ci')} CI)")
            return len(negatives)
        except: return 0

    async def _generate_daily_financial_report(self):
        """Gera resumo de transações das últimas 24h."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            # Entradas: PURCHASE (Vendas Stripe)
            in_res = db_client.client.table('ci_transactions').select('amount').eq('type', 'PURCHASE').gte('created_at', yesterday.isoformat()).execute()
            # Saídas: CONSUMPTION (Dossiês, Alvos, etc)
            out_res = db_client.client.table('ci_transactions').select('amount').eq('type', 'CONSUMPTION').gte('created_at', yesterday.isoformat()).execute()
            
            total_in = sum(t['amount'] for t in (in_res.data or []))
            total_out = abs(sum(t['amount'] for t in (out_res.data or [])))
            
            logger.info(f"📊 [Financeiro] Balanço {yesterday.date()}: +{total_in} CI (In) | -{total_out} CI (Out) | Líquido: {total_in - total_out} CI")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao gerar DRE: {e}")

    async def _compute_burn_rate(self):
        """Monitora o custo de processamento por alvo monitorado."""
        # TODO: Implementar mapeamento de tokens de IA para custo financeiro real
        pass
