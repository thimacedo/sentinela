"""
AutopilotManager — Orquestrador L3 do Sistema Sentinela (PASA v80.0)

Ciclo de vida (Loop OODA):
  1. Observar  → Coleta métricas reais do Supabase (worker_metrics)
  2. Orientar  → Compara contra baseline saudável (20% falha/vazio)
  3. Decidir   → Diagnostica causa raiz via IA (Diagnostician)
  4. Agir      → Aplica hot-fix no código (Patcher) ou aciona SessionHealer
"""
import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any

from core.supabase_service import get_supabase_client

logger = logging.getLogger("core.autopilot")


class AutopilotManager:
    """
    Orquestrador Autopilot L3 (PASA v80.0).
    Gerencia a saúde do sistema e toma decisões de recuperação automática.
    """

    def __init__(self, db_client=None):
        self.db = db_client or get_supabase_client()
        self.last_check = datetime.now(timezone.utc)
        self.last_preventive_heal = datetime.now(timezone.utc)
        self.failure_threshold = 0.20   # 20% de falha/vazio aciona intervenção
        self.is_active = True
        self._intervention_count = 0
        # Cooldown anti-detecção: mínimo 6h entre renovações reativas de sessão
        self.last_session_heal = datetime.now(timezone.utc).replace(year=2000)  # Força elegível no início

        # Inicializa submódulos de diagnóstico e correção
        try:
            from core.autopilot.diagnostician import Diagnostician
            from core.autopilot.patcher import Patcher
            self.diagnostician = Diagnostician()
            self.patcher = Patcher(project_root=os.getcwd())
        except Exception as e:
            logger.warning(f"⚠️ [Autopilot] Submódulos de diagnóstico indisponíveis: {e}")
            self.diagnostician = None
            self.patcher = None

    async def pulse(self):
        """Ciclo de vida do Autopilot — Loop OODA a cada 5 minutos."""
        while self.is_active:
            try:
                # 🛡️ CURA PREVENTIVA OPERACIONAL (PASA v84.3): Executada a cada 24 horas
                # Intervalo aumentado de 12h → 24h para evitar detecção por frequência de re-login
                now = datetime.now(timezone.utc)
                elapsed_preventive = (now - self.last_preventive_heal).total_seconds()
                if elapsed_preventive >= 86400:
                    logger.info("🔑 [Autopilot] Iniciando verificação preventiva periódica de cookies...")
                    try:
                        from core.autopilot.session_healer import SessionHealer
                        healer = SessionHealer()
                        # Roda sem force para apenas auditar e corrigir contas com sessões falhas
                        await healer.heal(force=False)
                        self.last_preventive_heal = now
                    except Exception as e_preventive:
                        logger.error(f"💥 [Autopilot] Erro na renovação preventiva de cookies: {e_preventive}")

                logger.info("🔍 [Autopilot] Iniciando pulso de diagnóstico...")
                metrics = await self._collect_recent_metrics()

                if metrics.get("failure_rate", 0) > self.failure_threshold:
                    logger.warning(
                        f"⚠️ [Autopilot] Taxa de falha crítica: {metrics['failure_rate']:.2%} "
                        f"(ciclos: {metrics['total_cycles']}, vazios: {metrics.get('empty_cycles', 0)})"
                    )
                    await self._handle_degradation(metrics)
                else:
                    logger.info(
                        f"✅ [Autopilot] Baseline saudável. "
                        f"Taxa de falha: {metrics['failure_rate']:.2%} / {metrics['total_cycles']} ciclos."
                    )

                self.last_check = datetime.now(timezone.utc)
                await asyncio.sleep(300)  # Pulso a cada 5 minutos

            except Exception as e:
                logger.error(f"💥 [Autopilot] Erro no ciclo de pulso: {e}")
                await asyncio.sleep(60)

    async def _collect_recent_metrics(self) -> Dict[str, Any]:
        """Coleta métricas dos ciclos posteriores ao último check."""
        try:
            res = self.db.table("worker_metrics")\
                .select("*")\
                .gt("timestamp", self.last_check.isoformat())\
                .execute()

            data = res.data or []
            if not data:
                return {"failure_rate": 0, "total_cycles": 0, "empty_cycles": 0, "errors": []}

            total_collected = sum(m.get("items_collected", 0) for m in data)
            total_failed = sum(m.get("items_failed", 0) for m in data)
            total_cycles = len(data)
            empty_cycles = sum(1 for m in data if m.get("items_collected", 0) == 0)
            all_errors = []
            for m in data:
                errs = m.get("errors") or []
                if isinstance(errs, list):
                    all_errors.extend(errs)

            total = total_collected + total_failed
            failure_rate = total_failed / total if total > 0 else 0
            empty_rate = empty_cycles / total_cycles if total_cycles > 0 else 0

            return {
                "failure_rate": max(failure_rate, empty_rate),
                "total_cycles": total_cycles,
                "empty_cycles": empty_cycles,
                "errors": all_errors,
            }
        except Exception as e:
            logger.error(f"❌ [Autopilot] Erro ao coletar métricas: {e}")
            return {"failure_rate": 0, "total_cycles": 0, "empty_cycles": 0, "errors": []}

    async def _handle_degradation(self, metrics: Dict[str, Any]):
        """Protocolo de intervenção baseado no diagnóstico de IA (OODA: Decidir → Agir)."""
        self._intervention_count += 1
        logger.info(f"🛠️ [Autopilot] Intervenção #{self._intervention_count} iniciada.")

        # Passo 1: Limpeza preventiva de processos órfãos
        try:
            from core.process_cleaner import cleanup_orphans
            cleanup_orphans()
        except Exception as e:
            logger.warning(f"⚠️ [Autopilot] Falha no cleanup: {e}")

        # Passo 2: Diagnóstico semântico via IA (se disponível)
        if self.diagnostician and metrics.get("errors"):
            log_segment = "\n".join(str(e) for e in metrics["errors"][:20])
            diagnosis = await self.diagnostician.analyze_log_segment(log_segment)
            error_type = diagnosis.get("type") or diagnosis.get("categoria_ia", "UNKNOWN")
            confidence = diagnosis.get("confidence") or diagnosis.get("confianca_ia", 0.0)

            logger.info(f"🧠 [Autopilot] Diagnóstico: {error_type} (confiança: {confidence:.2%})")
            self._log_event("autopilot_diagnosis", f"Tipo: {error_type}", {
                "diagnosis": diagnosis,
                "metrics": metrics,
                "intervention": self._intervention_count,
            })

            # Passo 3: Aplicar correção baseada no tipo de erro
            if error_type == "DOM_CHANGE" and confidence > 0.5 and self.patcher:
                await self._apply_dom_fix(diagnosis)

            elif error_type == "SESSION_EXPIRED":
                await self._trigger_session_healing()

            elif error_type == "IP_BLOCK":
                logger.warning("🛡️ [Autopilot] IP bloqueado detectado. Aumentando jitter para próximo ciclo.")
                os.environ["AUTOPILOT_FORCE_JITTER"] = "true"
        else:
            logger.info("🚀 [Autopilot] Intervenção básica (Cleanup) concluída. Sem dados de erro para diagnóstico semântico.")

    async def _apply_dom_fix(self, diagnosis: dict):
        """Tenta corrigir seletor CSS/XPath quebrado via IA + Patcher."""
        logger.info("🔧 [Autopilot] Tentando auto-corrigir seletor CSS via Patcher...")
        new_selector = diagnosis.get("new_selector") or diagnosis.get("analise_pericial", "")

        if new_selector and len(new_selector) > 5:
            old_selector = "div._aabd, div._ac7v div"  # Seletor atual do grid Instagram
            success = self.patcher.update_selector(
                scraper_file="core/instagram_scraper_v2.py",
                old_selector=old_selector,
                new_selector=new_selector
            )
            if success:
                logger.info(f"✅ [Autopilot] Hot-fix aplicado! Novo seletor: '{new_selector}'")
                self._log_event("hotfix_applied", f"Seletor atualizado para: {new_selector}", {
                    "old_selector": old_selector, "new_selector": new_selector
                })
            else:
                logger.warning("⚠️ [Autopilot] Hot-fix falhou. Seletor original não encontrado.")
        else:
            logger.warning("⚠️ [Autopilot] Diagnóstico não retornou seletor válido para correção automática.")

    async def _trigger_session_healing(self):
        """Aciona o SessionHealer para renovar sessões expiradas (com cooldown de 6h anti-detecção)."""
        now = datetime.now(timezone.utc)
        elapsed_heal = (now - self.last_session_heal).total_seconds()
        cooldown_seconds = 21600  # 6 horas
        
        if elapsed_heal < cooldown_seconds:
            remaining = int((cooldown_seconds - elapsed_heal) / 60)
            logger.warning(
                f"🕒 [Autopilot] SessionHealer em cooldown anti-detecção. "
                f"Próxima renovação disponível em ~{remaining} min. Aguardando..."
            )
            return
        
        logger.warning("🔑 [Autopilot] Sessão expirada detectada. Acionando SessionHealer com re-login forçado...")
        try:
            from core.autopilot.session_healer import SessionHealer
            healer = SessionHealer()
            success = await healer.heal(force=True)
            if success:
                self.last_session_heal = now
                logger.info("✅ [Autopilot] SessionHealer renovou as sessões com sucesso.")
                self._log_event("session_healer", "Sessões renovadas pelo SessionHealer (forçado).", {
                    "cooldown_next_available_minutes": cooldown_seconds // 60
                })
            else:
                logger.error("❌ [Autopilot] SessionHealer não conseguiu renovar as sessões. Intervenção humana necessária.")
                self._log_event("session_healer", "Falha na renovação de sessão. Requer ação manual.", {})
        except Exception as e:
            logger.error(f"💥 [Autopilot] Erro ao acionar SessionHealer: {e}")

    def _log_event(self, event_type: str, description: str, metadata: dict) -> None:
        """Registra evento de auditoria no Supabase."""
        try:
            self.db.table("system_events").insert({
                "event_type": event_type,
                "source": "local",
                "severity": "warning" if "falha" in description.lower() or "fail" in description.lower() else "info",
                "description": description,
                "metadata": metadata,
            }).execute()
        except Exception:
            pass  # Falha silenciosa — log não deve derrubar o autopilot

    def stop(self):
        self.is_active = False


autopilot = AutopilotManager()
