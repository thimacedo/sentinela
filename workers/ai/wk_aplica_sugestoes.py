"""
WkAplicaSugestoes — Consumidor de Sugestões do AIAdvisor (PASA v80.0)

Fecha o loop de feedback do AIAdvisor:
  AIAdvisor gera sugestão → WkAplicaSugestoes aplica automaticamente
  
Sugestões aplicáveis automaticamente:
  - Ajuste de max_posts (reduzir carga)
  - Ajuste de jitter (aumentar anonimato)
  - Desativação temporária de alvos específicos
  
Sugestões que requerem humano:
  - Alterações de lógica de classificação IA
  - Mudanças de seletores CSS (delega ao Patcher)
  - Troca de credenciais/sessões (delega ao SessionHealer)
"""
import asyncio
import logging
import re
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger("workers.ai.suggestion_consumer")


class WkAplicaSugestoes:
    """
    Lê sugestões pendentes do AIAdvisor e aplica as que são automatizáveis (PASA v80.0).
    Roda como task assíncrona no main_runner.
    """

    def __init__(self, db_client=None, orchestrator=None):
        from core.supabase_service import get_supabase_client
        self.db = db_client or get_supabase_client()
        self.orchestrator = orchestrator  # Referência ao orquestrador para ajustar configs
        self.is_active = True
        self._check_interval = 1800  # 30 minutos

    async def start(self) -> None:
        """Inicia o loop de verificação de sugestões."""
        logger.info("💡 [WkAplicaSugestoes] Iniciado. Verificando sugestões a cada 30 min.")
        while self.is_active:
            await asyncio.sleep(self._check_interval)
            await self._process_pending_suggestions()

    def stop(self) -> None:
        self.is_active = False

    async def _process_pending_suggestions(self) -> None:
        """Lê e processa sugestões pendentes do banco."""
        try:
            res = self.db.table("worker_suggestions")\
                .select("*")\
                .eq("status", "pending_review")\
                .order("timestamp", desc=False)\
                .limit(10)\
                .execute()

            suggestions = res.data or []
            if not suggestions:
                logger.debug("💡 [WkAplicaSugestoes] Nenhuma sugestão pendente.")
                return

            logger.info(f"💡 [WkAplicaSugestoes] {len(suggestions)} sugestão(ões) para processar.")

            for s in suggestions:
                await self._evaluate_and_apply(s)

        except Exception as e:
            logger.error(f"❌ [WkAplicaSugestoes] Erro ao ler sugestões: {e}")

    async def _evaluate_and_apply(self, suggestion: dict) -> None:
        """Avalia uma sugestão e decide se pode ser aplicada automaticamente."""
        sid = suggestion.get("id")
        text = suggestion.get("suggestion", "").lower()
        worker_id = suggestion.get("worker_id")

        action_taken = None
        new_status = "requires_human"

        # --- Padrão: Reduzir max_posts ---
        if any(p in text for p in ["reduzir max_posts", "diminuir posts", "reduce posts", "reduzir coleta"]):
            action_taken = await self._apply_config_change(worker_id, "max_posts", max(1, self._get_current_config(worker_id, "max_posts", 3) - 1))
            new_status = "auto_applied" if action_taken else "requires_human"

        # --- Padrão: Aumentar jitter ---
        elif any(p in text for p in ["aumentar jitter", "aumentar intervalo", "increase jitter", "espera maior"]):
            action_taken = f"Jitter aumentado para próximo ciclo via env AUTOPILOT_FORCE_JITTER"
            import os
            os.environ["AUTOPILOT_FORCE_JITTER"] = "true"
            new_status = "auto_applied"

        # --- Padrão: Seletor DOM — Delegar ao Patcher ---
        elif any(p in text for p in ["seletor", "selector", "dom mudou", "dom change", "css"]):
            action_taken = "Delegado ao AutopilotManager (Patcher) no próximo pulso."
            import os
            os.environ["AUTOPILOT_DOM_CHANGE_HINT"] = suggestion.get("suggestion", "")
            new_status = "auto_applied"

        # --- Padrão: Sessão expirada — Delegar ao SessionHealer ---
        elif any(p in text for p in ["sessão expirada", "session expired", "renovar sessão", "login"]):
            action_taken = "Delegado ao SessionHealer via AutopilotManager no próximo pulso."
            import os
            os.environ["AUTOPILOT_SESSION_EXPIRED_HINT"] = "true"
            new_status = "auto_applied"

        # --- Padrão: Desativar alvo temporariamente ---
        elif any(p in text for p in ["hibernar alvo", "desativar alvo", "pause target"]):
            username = self._extract_username(text)
            if username:
                action_taken = await self._hibernate_target(username)
                new_status = "auto_applied" if action_taken else "requires_human"

        # Atualiza status da sugestão no banco
        try:
            update_data = {
                "status": new_status,
            }
            if action_taken:
                update_data["suggestion"] = f"[{new_status.upper()}] {action_taken}\n\nOriginal: {suggestion.get('suggestion', '')}"

            self.db.table("worker_suggestions").update(update_data).eq("id", sid).execute()

            if new_status == "auto_applied":
                logger.info(f"✅ [WkAplicaSugestoes] Sugestão #{sid} aplicada automaticamente: {action_taken}")
            else:
                logger.info(f"👤 [WkAplicaSugestoes] Sugestão #{sid} requer revisão humana.")

        except Exception as e:
            logger.error(f"❌ [WkAplicaSugestoes] Erro ao atualizar sugestão #{sid}: {e}")

    async def _apply_config_change(self, worker_id: str, param: str, new_value) -> Optional[str]:
        """Tenta ajustar a config de um worker registrado no orquestrador."""
        if not self.orchestrator:
            logger.warning("⚠️ [WkAplicaSugestoes] Sem referência ao orquestrador. Config não pode ser ajustada.")
            return None

        for worker in getattr(self.orchestrator, "_workers", []):
            if worker.worker_id == worker_id:
                old_value = worker.config.get(param)
                worker.config[param] = new_value
                msg = f"Config '{param}' de {worker_id}: {old_value} → {new_value}"
                logger.info(f"⚙️ [WkAplicaSugestoes] {msg}")
                return msg

        return None

    def _get_current_config(self, worker_id: str, param: str, default) -> int:
        """Lê config atual de um worker."""
        if not self.orchestrator:
            return default
        for worker in getattr(self.orchestrator, "_workers", []):
            if worker.worker_id == worker_id:
                return worker.config.get(param, default)
        return default

    async def _hibernate_target(self, username: str) -> Optional[str]:
        """Move um alvo para status FRIO temporariamente."""
        try:
            self.db.table("fila_coleta").update({
                "status": "HIBERNANDO",
                "prioridade": 9,
            }).eq("username", username).execute()
            return f"Alvo @{username} movido para HIBERNANDO."
        except Exception as e:
            logger.error(f"❌ [WkAplicaSugestoes] Erro ao hibernar @{username}: {e}")
            return None

    def _extract_username(self, text: str) -> Optional[str]:
        """Extrai @username de um texto de sugestão."""
        match = re.search(r'@([\w.]+)', text)
        return match.group(1) if match else None
