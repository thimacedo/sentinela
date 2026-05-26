import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

from core.supabase_service import get_supabase_client

logger = logging.getLogger("core.autopilot")

class AutopilotManager:
    """
    Orquestrador Autopilot (PASA v70.0 - L3).
    Gerencia a saúde do sistema e toma decisões de recuperação automática.
    """
    def __init__(self, db_client=None):
        self.db = db_client or get_supabase_client()
        self.last_check = datetime.now(timezone.utc)
        self.failure_threshold = 0.2  # 20% de falha/vazio
        self.is_active = True

    async def pulse(self):
        """Ciclo de vida do Autopilot."""
        while self.is_active:
            try:
                logger.info("🔍 [Autopilot] Iniciando pulso de diagnóstico...")
                metrics = await self._collect_recent_metrics()
                
                if metrics.get("failure_rate", 0) > self.failure_threshold:
                    logger.warning(f"⚠️ [Autopilot] Taxa de falha crítica detectada: {metrics['failure_rate']:.2f}")
                    await self._handle_degradation(metrics)
                else:
                    logger.info("✅ [Autopilot] Sistema operando dentro da baseline saudável.")
                
                await asyncio.sleep(300) # Pulso a cada 5 minutos
            except Exception as e:
                logger.error(f"💥 [Autopilot] Erro no ciclo de pulso: {e}")
                await asyncio.sleep(60)

    async def _collect_recent_metrics(self) -> Dict[str, Any]:
        """Coleta métricas dos últimos 60 minutos do Supabase."""
        try:
            # Busca métricas reais da tabela worker_metrics
            res = self.db.table("worker_metrics")\
                .select("*")\
                .gt("timestamp", self.last_check.isoformat())\
                .execute()
            
            data = res.data or []
            if not data:
                return {"failure_rate": 0, "total_cycles": 0}
            
            total_collected = sum(m.get("items_collected", 0) for m in data)
            total_failed = sum(m.get("items_failed", 0) for m in data)
            total_cycles = len(data)
            
            failure_rate = total_failed / (total_collected + total_failed) if (total_collected + total_failed) > 0 else 0
            
            # Detecção de Vazios (extracted=0)
            empty_cycles = sum(1 for m in data if m.get("items_collected", 0) == 0)
            empty_rate = empty_cycles / total_cycles if total_cycles > 0 else 0
            
            return {
                "failure_rate": max(failure_rate, empty_rate),
                "total_cycles": total_cycles,
                "empty_cycles": empty_cycles
            }
        except Exception as e:
            logger.error(f"❌ [Autopilot] Erro ao coletar métricas: {e}")
            return {"failure_rate": 0, "total_cycles": 0}

    async def _handle_degradation(self, metrics: Dict[str, Any]):
        """Decide a intervenção baseada nas métricas."""
        logger.info("🛠️ [Autopilot] Iniciando protocolo de intervenção...")
        
        # 1. Tenta limpar processos órfãos primeiro
        from core.process_cleaner import cleanup_orphans
        cleanup_orphans()
        
        # 2. Se a falha persistir, pode sinalizar necessidade de troca de sessões
        # (Lógica futura: rotation de proxies ou sessões)
        logger.info("🚀 [Autopilot] Intervenção básica (Cleanup) concluída. Monitorando próximo ciclo.")

    def stop(self):
        self.is_active = False

autopilot = AutopilotManager()
