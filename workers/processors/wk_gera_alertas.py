# workers/processors/alert_worker.py
from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Migrado de workers.core.base_worker (legado) → workers.base.worker_base (PASA v88.0)
from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.supabase_service import get_supabase_client

# Firebase Admin para FCM
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False


class WkGeraAlertas(BaseWorker):
    """
    Sub-agente de monitoramento e alertas.
    Observa a saúde do sistema e dispara notificações FCM/Webhook
    quando detecta anomalias. Roda a cada 5 minutos via Tray ou Main Runner.

    Migrado para BaseWorker moderno (PASA v88.0) — usa run_cycle() + CycleResult.
    """

    SEVERITY_EMOJI = {
        "critical": "🚨",
        "warning":  "⚠️",
        "info":     "ℹ️",
    }

    def __init__(self, worker_id: str = "alert_worker", config: dict = None):
        super().__init__(worker_id, config or {})
        self.cycle = 0
        self.db = get_supabase_client()
        self._init_firebase()

    def _init_firebase(self) -> None:
        if not _FIREBASE_AVAILABLE:
            self.logger.warning(
                "firebase_admin não instalado. "
                "Notificações FCM desabilitadas."
            )
            self.fcm_enabled = False
            return

        try:
            if not firebase_admin._apps:
                sa_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
                if not sa_key:
                    self.fcm_enabled = False
                    return
                service_account = json.loads(sa_key)
                cred = credentials.Certificate(service_account)
                firebase_admin.initialize_app(cred)
            self.fcm_enabled = True
            self.logger.info("✅ Firebase Admin inicializado.")
        except Exception as exc:
            self.logger.error(f"Falha ao inicializar Firebase: {exc}")
            self.fcm_enabled = False

    def describe(self) -> str:
        return "WkGeraAlertas — Monitor de Anomalias e Notificações FCM/Webhook"

    async def setup(self) -> None:
        self.logger.info("✅ [WkGeraAlertas] Inicializado. FCM=%s", self.fcm_enabled)

    async def teardown(self) -> None:
        self.logger.info("🛑 [WkGeraAlertas] Encerrado.")

    async def run_cycle(self) -> CycleResult:
        """Ciclo principal: detecta anomalias e dispara alertas."""
        import asyncio as _aio
        start = _aio.get_event_loop().time()
        self.cycle += 1

        if self.shutdown_event and self.shutdown_event.is_set():
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="alert", error="shutdown_requested",
                duration=_aio.get_event_loop().time() - start,
            )

        # 1. Detecta anomalias via SQL
        anomalies = self._detect_anomalies()

        if not anomalies:
            self.logger.info("✅ [WkGeraAlertas] Sistema saudável. Nenhuma anomalia detectada.")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="alert", error="no_tasks_available",
                duration=_aio.get_event_loop().time() - start,
            )

        self.logger.warning("⚠️ [WkGeraAlertas] %d anomalia(s) detectada(s).", len(anomalies))

        # 2. Para cada anomalia, decide se notifica
        fired = []
        for anomaly in anomalies:
            alert = self._upsert_alert(anomaly)
            if alert and not alert.get("notified"):
                await self._notify(alert)
                fired.append(alert)

        # 3. Resolve alertas antigos que se normalizaram
        self._resolve_stale_alerts(anomalies)

        return CycleResult(
            worker_id=self.worker_id, cycle=self.cycle,
            source="alert",
            extracted=len(anomalies),
            inserted=len(fired),
            db_success=True,
            simulated=False,
            duration=_aio.get_event_loop().time() - start,
            metadata={"anomalies": len(anomalies), "fired": len(fired)},
        )

    async def _run(self, payload: dict) -> list:
        """Mantido para retrocompatibilidade com chamadas legadas (workers.core.BaseWorker)."""
        result = await self.run_cycle()
        return result.metadata.get("fired", [])

    def _detect_anomalies(self) -> list[dict]:
        try:
            res = self.db.rpc("detect_worker_anomalies").execute()
            return res.data or []
        except Exception as exc:
            self.logger.error(f"Erro ao detectar anomalias: {exc}")
            return []

    def _upsert_alert(self, anomaly: dict) -> dict | None:
        """
        Insere ou recupera alerta existente.
        O UNIQUE constraint evita duplicatas — se já existe alerta
        não resolvido do mesmo tipo, apenas retorna ele.
        """
        try:
            res = self.db.table("system_alerts").upsert({
                "worker_name":   anomaly["worker_name"],
                "anomaly_type":  anomaly["anomaly_type"],
                "severity":      anomaly["severity"],
                "current_value": anomaly["current_value"],
                "threshold":     anomaly["threshold"],
                "message":       anomaly["suggested_action"],
                "resolved":      False,
            }, on_conflict="worker_name,anomaly_type,resolved").execute()

            return res.data[0] if res.data else None
        except Exception as exc:
            self.logger.error(f"Erro ao upsert alerta: {exc}")
            return None

    async def _notify(self, alert: dict) -> None:
        """Dispara notificação FCM e marca como notificado."""
        severity = alert.get("severity", "warning")
        emoji = self.SEVERITY_EMOJI.get(severity, "⚠️")
        worker = alert.get("worker_name", "Sistema")
        anomaly = alert.get("anomaly_type", "ANOMALIA")
        message = alert.get("message", "Verifique o sistema.")

        title = f"{emoji} Sentinela — {severity.upper()}"
        body  = f"[{worker}] {anomaly}: {message}"

        self.logger.warning(f"📣 Disparando alerta: {title} | {body}")

        # FCM para todos os tokens registrados
        if self.fcm_enabled:
            await self._send_fcm(title, body, alert)

        # Webhook como fallback (Slack, Discord, etc.)
        webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        if webhook_url:
            await self._send_webhook(webhook_url, title, body, severity)

        # Marca como notificado
        try:
            self.db.table("system_alerts").update({
                "notified": True
            }).eq("id", alert["id"]).execute()
        except Exception as exc:
            self.logger.error(f"Erro ao marcar alerta como notificado: {exc}")

    async def _send_fcm(self, title: str, body: str, alert: dict) -> None:
        """Busca todos os push tokens e envia notificação multicast."""
        try:
            # Busca tokens dos usuários admin
            tokens_res = self.db.table("profiles") \
                .select("push_token") \
                .not_.is_("push_token", "null") \
                .execute()

            tokens = [
                row["push_token"]
                for row in (tokens_res.data or [])
                if row.get("push_token")
            ]

            if not tokens:
                self.logger.warning("Nenhum push token registrado.")
                return

            message = messaging.MulticastMessage(
                tokens=tokens,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "alert_id":     str(alert.get("id", "")),
                    "anomaly_type": alert.get("anomaly_type", ""),
                    "severity":     alert.get("severity", ""),
                    "worker_name":  alert.get("worker_name", ""),
                },
            )

            response = messaging.send_each_for_multicast(message)
            self.logger.info(
                f"FCM: {response.success_count} entregues, "
                f"{response.failure_count} falhas."
            )

            # Remove tokens inválidos automaticamente
            if response.failure_count:
                await self._cleanup_invalid_tokens(tokens, response.responses)

        except Exception as exc:
            self.logger.error(f"Erro ao enviar FCM: {exc}")

    async def _send_webhook(
        self, url: str, title: str, body: str, severity: str
    ) -> None:
        """Payload compatível com Slack e Discord simultaneamente."""
        colors = {"critical": "#ef4444", "warning": "#f59e0b", "info": "#3b82f6"}
        color = colors.get(severity, "#6b7280")

        # Slack
        slack_payload = {
            "attachments": [{
                "color":  color,
                "title":  title,
                "text":   body,
                "footer": f"Sentinela PASA v17 | {datetime.now(UTC).strftime('%H:%M UTC')}",
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=slack_payload)
                self.logger.info(f"Webhook enviado para {url.split('/')[2]}")
        except Exception as exc:
            self.logger.error(f"Erro ao enviar webhook: {exc}")

    async def _cleanup_invalid_tokens(
        self, tokens: list[str], responses: list
    ) -> None:
        """Remove do banco tokens que o FCM reportou como inválidos."""
        invalid = [
            tokens[i]
            for i, resp in enumerate(responses)
            if not resp.success
        ]
        if invalid:
            self.db.table("profiles") \
                .update({"push_token": None}) \
                .in_("push_token", invalid) \
                .execute()
            self.logger.info(
                f"🧹 {len(invalid)} tokens inválidos removidos."
            )

    def _resolve_stale_alerts(self, current_anomalies: list[dict]) -> None:
        """
        Marca como resolvidos alertas que não aparecem mais
        na detecção atual — o problema foi corrigido.
        """
        active_keys = {
            (a["worker_name"], a["anomaly_type"])
            for a in current_anomalies
        }

        try:
            open_alerts = self.db.table("system_alerts") \
                .select("id, worker_name, anomaly_type") \
                .eq("resolved", False) \
                .execute().data or []

            for alert in open_alerts:
                key = (alert["worker_name"], alert["anomaly_type"])
                if key not in active_keys:
                    self.db.table("system_alerts").update({
                        "resolved":     True,
                        "resolved_at":  datetime.now(UTC).isoformat(),
                    }).eq("id", alert["id"]).execute()
                    self.logger.info(
                        f"✅ Alerta resolvido: [{alert['worker_name']}] "
                        f"{alert['anomaly_type']}"
                    )
        except Exception as exc:
            self.logger.error(f"Erro ao resolver alertas: {exc}")


if __name__ == "__main__":
    asyncio.run(WkGeraAlertas().execute({}))
