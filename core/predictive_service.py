import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import numpy as np
from core.db import db_client
from core.firebase_alerter import send_alert_summary

logger = logging.getLogger("PredictiveService")

class PredictiveService:
    """
    Motor de análise preditiva para o Sentinela Democrática.
    Analisa séries temporais de hostilidade para prever surtos de ataques coordenados.
    """
    
    def __init__(self, threshold_std: float = 2.0):
        self.threshold_std = threshold_std

    async def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Busca dados históricos e identifica anomalias ou tendências de crescimento.
        """
        logger.info(f"📈 [Predictive] Analisando tendências dos últimos {days} dias...")
        
        # 1. Busca dados temporais do banco
        # Nota: Idealmente usaríamos a tabela de métricas diárias, 
        # mas vamos agregar dos comentários para maior precisão granular.
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=days)).isoformat()
        
        try:
            # Busca contagem de ódio agrupada por hora (via Supabase RPC ou fetch + process)
            # Para este MVP, vamos buscar os últimos 1000 comentários de ódio e agrupar
            from core.constants import HATE_CATEGORIES
            res = db_client.client.table('comentarios')\
                .select('data_coleta')\
                .in_('categoria_ia', HATE_CATEGORIES)\
                .gte('data_coleta', start_date)\
                .execute()
            
            data = res.data or []
            if len(data) < 10:
                return {"status": "insufficient_data", "trend": "stable"}

            # Agrupamento por hora
            series = {}
            for item in data:
                hour = item['data_coleta'][:13] # YYYY-MM-DDTHH
                series[hour] = series.get(hour, 0) + 1
            
            # Ordenação cronológica
            sorted_hours = sorted(series.keys())
            counts = [series[h] for h in sorted_hours]
            
            # 2. Análise Estatística
            mean = np.mean(counts)
            std = np.std(counts)
            current = counts[-1] if counts else 0
            
            # 3. Projeção Simples (Regressão Linear de 1º grau)
            x = np.arange(len(counts))
            y = np.array(counts)
            slope, intercept = np.polyfit(x, y, 1)
            
            projection_next_24h = slope * (len(counts) + 24) + intercept
            
            # 4. Detecção de Anomalia
            is_anomaly = False
            if current > (mean + self.threshold_std * std) and current > 5:
                is_anomaly = True
                
            status = {
                "mean_hourly": float(mean),
                "current_hourly": int(current),
                "std_dev": float(std),
                "slope": float(slope),
                "is_anomaly": is_anomaly,
                "projected_24h_level": float(max(0, projection_next_24h)),
                "trend": "rising" if slope > 0.1 else ("falling" if slope < -0.1 else "stable")
            }
            
            if is_anomaly or (status['trend'] == "rising" and status['projected_24h_level'] > mean * 2):
                await self._trigger_predictive_alert(status)
                
            return status

        except Exception as e:
            logger.error(f"❌ [Predictive] Erro ao analisar tendências: {e}")
            return {"status": "error", "message": str(e)}

    async def _trigger_predictive_alert(self, status: Dict[str, Any]):
        """Dispara notificações preventivas para a equipe."""
        msg = (
            f"🚨 ALERTAS PREDITIVOS (Diamond Engine)\n"
            f"📈 Tendência: {status['trend'].upper()}\n"
            f"⚠️ Risco de Pico: Nível projetado {status['projected_24h_level']:.1f}/h\n"
            f"📊 Média atual: {status['mean_hourly']:.1f}/h\n"
            f"🔍 Status: ANOMALIA DETECTADA" if status['is_anomaly'] else "🔍 Status: ALERTA PREVENTIVO"
        )
        
        logger.warning(f"🔔 [Predictive] Disparando alerta: {msg}")
        # await send_alert_summary(msg) # Desativado em dev para evitar spam
        
        # Persiste o alerta no banco
        await db_client.create_active_alert({
            "tipo": "PREDITIVO",
            "severidade": "ALTA" if status['is_anomaly'] else "MEDIA",
            "mensagem": msg,
            "metadados": status
        })

predictive_service = PredictiveService()
