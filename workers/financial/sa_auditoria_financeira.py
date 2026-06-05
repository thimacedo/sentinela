import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple
from core.db import db_client

logger = logging.getLogger("SaAuditoriaFinanceira")

class SaAuditoriaFinanceira:
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
        logger.info("[SaAuditoriaFinanceira] Iniciando auditoria financeira do ecossistema Sentinela")
        start_time = asyncio.get_event_loop().time()

        anomalies = 0
        stripe_online = False
        stripe_has_key = False
        report_generated = False
        ai_burn_rate_usd = 0.0
        error = None

        try:
            # 1. Auditoria de Saldos Inconsistentes
            anomalies = await self.audit_balances()
            
            # 2. Conectividade com Stripe
            stripe_online, stripe_has_key = await self.check_stripe_connectivity()

            # 3. Mapeamento de Custos de IA (Burn Rate)
            ai_burn_rate_usd = await self._compute_burn_rate()

            # 4. Fechamento diário
            now = datetime.now(timezone.utc)
            if not self.daily_report_last_run or self.daily_report_last_run.date() < now.date():
                await self.generate_daily_financial_report()
                self.daily_report_last_run = now
                report_generated = True

        except Exception as e:
            logger.error(f"[SaAuditoriaFinanceira] Erro durante auditoria financeira: {e}", exc_info=True)
            error = str(e)

        duration = asyncio.get_event_loop().time() - start_time
        return {
            "success": error is None,
            "duration_seconds": round(duration, 2),
            "anomalies_detected": anomalies,
            "stripe_online": stripe_online,
            "stripe_has_key": stripe_has_key,
            "ai_burn_rate_usd": ai_burn_rate_usd,
            "report_generated": report_generated,
            "error": error
        }

    async def audit_balances(self) -> int:
        """Verifica perfis com saldos inconsistentes (negativos)."""
        try:
            res = db_client.client.table('profiles').select('id, saldo_ci').lt('saldo_ci', 0).execute()
            negatives = res.data or []
            
            for profile in negatives:
                logger.error(f"🚨 [SaAuditoriaFinanceira] Inconsistência de saldo encontrada: ID {profile.get('id')} ({profile.get('saldo_ci')} CI)")
            
            return len(negatives)
        except Exception as e:
            logger.error(f"[SaAuditoriaFinanceira] Falha na auditoria de saldos no DB: {e}")
            raise

    async def check_stripe_connectivity(self) -> Tuple[bool, bool]:
        """Testa se a API Key do Stripe está ativa e funcional."""
        import stripe
        stripe_key = os.getenv("STRIPE_API_KEY")
        if not stripe_key:
            logger.info("[SaAuditoriaFinanceira] Stripe API Key ausente. Rodando em modo simulado/mock.")
            return False, False

        stripe.api_key = stripe_key
        try:
            # Tenta listar o balanço básico para validar a chave de API
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, stripe.Balance.retrieve)
            logger.info("✅ [SaAuditoriaFinanceira] Conexão com gateway Stripe operando normalmente.")
            return True, True
        except Exception as e:
            logger.error(f"[SaAuditoriaFinanceira] Falha ao conectar ao gateway Stripe: {e}")
            return False, True

    async def _compute_burn_rate(self) -> float:
        """
        Consulta os logs de fallback das últimas 24 horas no banco de dados
        e calcula o burn rate (custo operacional estimado em USD).
        """
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1))
        
        provider_prices = {
            "cohere": 0.0001,
            "cohere_command": 0.0001,
            "deepseek": 0.00015,
            "deepseek_chat": 0.00015,
            "openai_gpt35": 0.0015,
            "openai": 0.01,
            "anthropic_claude_instant": 0.003,
            "google_gemini": 0.000075,
            "groq_llama3": 0.0001,
            "zhipu_glm4": 0.0001,
            "cerebras_llama3": 0.00005,
            "eden_ai": 0.001,
            "fireworks": 0.0001,
            "fireworks_ai": 0.0001,
            "openrouter": 0.0005,
        }
        
        total_cost = 0.0
        try:
            # Consulta a tabela fallback_logs para obter as chamadas desde ontem
            res = db_client.client.table('fallback_logs').select('provider, status').gte('timestamp', yesterday.isoformat()).execute()
            logs = res.data or []
            
            for log in logs:
                prov = log.get('provider')
                # Ignora watchdog_health ou logs genéricos que não consomem créditos de produção real de comentários
                if prov == 'watchdog':
                    continue
                cost = provider_prices.get(prov, 0.0001)  # Custo padrão de $0.0001 por chamada se desconhecido
                total_cost += cost
                
            logger.info(f"💸 [SaAuditoriaFinanceira] Burn Rate calculado nas últimas 24h: {len(logs)} chamadas | Custo Estimado = ${total_cost:.5f} USD")
            return round(total_cost, 5)
        except Exception as e:
            logger.error(f"[SaAuditoriaFinanceira] Erro ao calcular burn rate no DB: {e}")
            return 0.0

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
            
            # Aqui calculamos o custo real de IA nas últimas 24h
            burn_rate = await self._compute_burn_rate()

            logger.info(f"📊 [SaAuditoriaFinanceira] DRE Fechamento {yesterday.date()}: Inflow={total_in} CI | Outflow={total_out} CI | Net={net_flow} CI | AI Burn Cost=${burn_rate:.5f} USD")
        except Exception as e:
            logger.error(f"[SaAuditoriaFinanceira] Erro ao consolidar relatório diário DRE: {e}")
            raise
