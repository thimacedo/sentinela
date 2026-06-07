"""
WkAplicaSugestoes — Consumidor de Sugestões do AIAdvisor (PASA v93.0)

Fecha o loop de feedback do AIAdvisor:
  AIAdvisor gera sugestão → WkAplicaSugestoes aplica automaticamente
  
Este componente roda como uma tarefa de fundo (background task) independente do orquestrador.
"""
import asyncio
import logging
import re
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from workers.base.memory_store import MemoryStore
from core.db import db_client

logger = logging.getLogger("WkAplicaSugestoes")

class WkAplicaSugestoes:
    """
    Lê sugestões pendentes do AIAdvisor e aplica as que são automatizáveis.
    PASA v93.0: Restaurado como Background Task (sem herança de BaseWorker).
    """

    def __init__(
        self, 
        db_client_override=None,
        orchestrator=None,
        memory: Optional[MemoryStore] = None
    ):
        self.db = db_client_override or db_client.client
        self.orchestrator = orchestrator
        self.memory = memory or MemoryStore()
        self.is_active = True
        self._check_interval = 1800  # 30 minutos

    async def start(self):
        """Inicia o loop infinito de processamento de sugestões."""
        logger.info("💡 [WkAplicaSugestoes] Iniciando loop de feedback automático...")
        while self.is_active:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Erro no ciclo de sugestões: {e}")
            
            await asyncio.sleep(self._check_interval)

    async def run_cycle(self):
        """Executa um ciclo de busca e aplicação de sugestões."""
        # 1. Busca sugestões pendentes
        res = await asyncio.to_thread(
            self.db.table("worker_suggestions")
            .select("*")
            .eq("status", "pending_review")
            .order("timestamp", desc=False)
            .limit(5)
            .execute
        )

        suggestions = res.data or []
        if not suggestions:
            return

        applied_count = 0
        for s in suggestions:
            success = await self._evaluate_and_apply(s)
            if success: applied_count += 1
            
        if applied_count > 0:
            logger.info(f"⚡ [WkAplicaSugestoes] {applied_count} sugestões aplicadas automaticamente.")

    async def _evaluate_and_apply(self, suggestion: dict) -> bool:
        """Avalia uma sugestão e decide se pode ser aplicada automaticamente."""
        sid = suggestion.get("id")
        text = suggestion.get("suggestion", "").lower()
        target_worker_id = suggestion.get("worker_id")

        action_taken = None
        new_status = "requires_human"

        # --- Padrão: Reduzir max_posts ---
        if any(p in text for p in ["reduzir max_posts", "diminuir posts", "reduce posts", "reduzir coleta"]):
            action_taken = await self._apply_config_change(target_worker_id, "max_posts", max(1, self._get_current_config(target_worker_id, "max_posts", 3) - 1))
            new_status = "auto_applied" if action_taken else "requires_human"

        # --- Padrão: Aumentar jitter ---
        elif any(p in text for p in ["aumentar jitter", "aumentar intervalo", "increase jitter", "espera maior"]):
            action_taken = "Jitter aumentado via MemoryStore flag (v93.0)."
            await self.memory.set_flag("AUTOPILOT_FORCE_JITTER", True, ttl=3600)
            new_status = "auto_applied"

        # --- Padrão: Seletor DOM ---
        elif any(p in text for p in ["seletor", "selector", "dom mudou", "dom change", "css"]):
            action_taken = "Delegado ao Autopilot via MemoryStore hint."
            await self.memory.set_flag("AUTOPILOT_DOM_CHANGE_HINT", suggestion.get("suggestion"), ttl=1800)
            new_status = "auto_applied"

        # --- Padrão: Sessão expirada ---
        elif any(p in text for p in ["sessão expirada", "session expired", "renovar sessão", "login"]):
            action_taken = "Flag de sessão expirada enviada ao Healer."
            await self.memory.set_flag("AUTOPILOT_SESSION_EXPIRED", True, ttl=1800)
            new_status = "auto_applied"

        # --- Padrão: Desativar alvo temporariamente ---
        elif any(p in text for p in ["hibernar alvo", "desativar alvo", "pause target"]):
            username = self._extract_username(text)
            if username:
                action_taken = await self._hibernate_target(username)
                new_status = "auto_applied" if action_taken else "requires_human"

        # Atualiza status da sugestão no banco
        try:
            update_data = {"status": new_status}
            if action_taken:
                update_data["suggestion"] = f"[{new_status.upper()}] {action_taken}\n\n{suggestion.get('suggestion', '')}"

            await asyncio.to_thread(
                self.db.table("worker_suggestions").update(update_data).eq("id", sid).execute
            )
            return new_status == "auto_applied"
        except Exception as e:
            logger.error(f"Erro ao atualizar sugestão #{sid}: {e}")
            return False

    async def _apply_config_change(self, worker_id: str, param: str, new_value) -> Optional[str]:
        if not self.orchestrator: return None
        for worker in getattr(self.orchestrator, "_workers", []):
            if worker.worker_id == worker_id:
                old_value = worker.config.get(param)
                worker.config[param] = new_value
                return f"Config '{param}' de {worker_id}: {old_value} → {new_value}"
        return None

    def _get_current_config(self, worker_id: str, param: str, default) -> Any:
        if not self.orchestrator: return default
        for worker in getattr(self.orchestrator, "_workers", []):
            if worker.worker_id == worker_id:
                return worker.config.get(param, default)
        return default

    async def _hibernate_target(self, username: str) -> Optional[str]:
        try:
            await asyncio.to_thread(
                self.db.table("fila_coleta").update({
                    "status": "HIBERNANDO",
                    "prioridade": 9,
                }).eq("username", username).execute
            )
            return f"Alvo @{username} movido para HIBERNANDO."
        except Exception as e:
            logger.error(f"Erro ao hibernar @{username}: {e}")
            return None

    def _extract_username(self, text: str) -> Optional[str]:
        match = re.search(r'@([\w.]+)', text)
        return match.group(1) if match else None

    def stop(self):
        self.is_active = False
