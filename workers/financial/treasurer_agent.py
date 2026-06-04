import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple
from core.db import db_client

logger = logging.getLogger("TreasurerAgent")

class TreasurerAgent:
    """
    Subagente financeiro de auditoria analítica e fechamento financeiro diário.
    Monitora a conformidade do fluxo de CI e o status dos gateways de pagamento.
    PASA v88.1
    """

    def __init__(self):
        self.daily_report_last_run = None

    async def run_financial_audit(self) -> Dict[str, Any]:
        """
        Executa uma rodada completa de auditorias financeiras sob demanda:
        1. Auditoria de saldos inconsistentes (negativos).
        2. Teste de conectividade com Stripe.
        3. Geração de DRE/fechamento diário (se aplicável).
        """
        logger.info("[TreasurerAgent] Iniciando auditoria financeira do ecossistema Sentinela")
        start_time = asyncio.get_event_loop().time()

        anomalies = 0
        stripe_online = False
        stripe_has_key = False
        report_generated = False
        error = None

        try:
            # 1. Auditoria de Saldos Inconsistentes
            anomalies = await self.audit_balances()
            
            # 2. Conectividade com Stripe
            stripe_online, stripe_has_key = await self.check_stripe_connectivity()

            # 3. Fechamento diário
            now = datetime.now(timezone.utc)
            if not self.daily_report_last_run or self.daily_report_last_run.date() < now.date():
                await self.generate_daily_financial_report()
                self.daily_report_last_run = now
                report_generated = True

        except Exception as e:
            logger.error(f"[TreasurerAgent] Erro durante auditoria financeira: {e}", exc_info=True)
            error = str(e)

        duration = asyncio.get_event_loop().time() - start_time
        return {
            "success": error is None,
            "duration_seconds": round(duration, 2),
            "anomalies_detected": anomalies,
            "stripe_online": stripe_online,
            "stripe_has_key": stripe_has_key,
            "report_generated": report_generated,
            "error": error
        }

    async def audit_balances(self) -> int:
        """Verifica perfis com saldos inconsistentes (negativos)."""
        try:
            res = db_client.client.table('profiles').select('id, saldo_ci').lt('saldo_ci', 0).execute()
            negatives = res.data or []
            
            for profile in negatives:
                logger.error(f"🚨 [TreasurerAgent] Inconsistência de saldo encontrada: ID {profile.get('id')} ({profile.get('saldo_ci')} CI)")
            
            return len(negatives)
        except Exception as e:
            logger.error(f"[TreasurerAgent] Falha na auditoria de saldos no DB: {e}")
            raise

    async def check_stripe_connectivity(self) -> Tuple[bool, bool]:
        """Testa se a API Key do Stripe está ativa e funcional."""
        import stripe
        stripe_key = os.getenv("STRIPE_API_KEY")
        if not stripe_key:
            logger.info("[TreasurerAgent] Stripe API Key ausente. Rodando em modo simulado/mock.")
            return False, False

        stripe.api_key = stripe_key
        try:
            # Tenta listar o balanço básico para validar a chave de API
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, stripe.Balance.retrieve)
            logger.info("✅ [TreasurerAgent] Conexão com gateway Stripe operando normalmente.")
            return True, True
        except Exception as e:
            logger.error(f"[TreasurerAgent] Falha ao conectar ao gateway Stripe: {e}")
            return False, True

    async def generate_daily_financial_report(self) -> None:
        """Processa e consolida o fluxo financeiro de CI (Inflow/Outflow) das últimas 24h."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            # Compras / Inflow
            in_res = db_client.client.table('ci_transactions').select('amount').eq('type', 'PURCHASE').gte('created_at', yesterday.isoformat()).execute()
            # Consumo / Outflow
            out_res = db_client.client.table('ci_transactions').select('amount').eq('type', 'CONSUMPTION').gte('created_at', yesterday.isoformat()).execute()

            total_in = sum(t['amount'] for t in (in_res.data or []))
            total_out = abs(sum(t['amount'] for t in (out_res.data or [])))
            net_flow = total_in - total_out

            logger.info(f"📊 [TreasurerAgent] DRE Fechamento {yesterday.date()}: Inflow={total_in} CI | Outflow={total_out} CI | Net={net_flow} CI")
        except Exception as e:
            logger.error(f"[TreasurerAgent] Erro ao consolidar relatório diário DRE: {e}")
            raise
