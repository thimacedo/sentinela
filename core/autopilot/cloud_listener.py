"""
CloudListener — Heartbeat e Controle Remoto via Supabase (PASA v80.0)

Responsabilidades:
  - Publicar heartbeat a cada 60s na tabela system_heartbeat
  - Escutar tabela system_commands via polling (30s)
  - Reagir a comandos: PAUSE, RESUME, RESTART, UPDATE, FORCE_SCRAPE
"""
import asyncio
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional, Callable

logger = logging.getLogger("core.autopilot.cloud_listener")

# Estado global de controle (compartilhado com o watchdog/runner)
_is_paused = False
_current_cycle = 0
_restart_requested = False


def set_current_cycle(cycle: int) -> None:
    """Atualiza o ciclo atual do worker para o heartbeat."""
    global _current_cycle
    _current_cycle = cycle


def is_paused() -> bool:
    """Verifica se o sistema está pausado por comando remoto."""
    return _is_paused


def restart_was_requested() -> bool:
    """Verifica se um restart foi solicitado remotamente."""
    global _restart_requested
    if _restart_requested:
        _restart_requested = False
        return True
    return False


class CloudListener:
    """
    Listener de Controle Remoto e Heartbeat (PASA v80.0).
    Roda como coroutine assíncrona em background.
    """

    def __init__(self, db_client=None, source: str = "local"):
        from core.supabase_service import get_supabase_client
        self.db = db_client or get_supabase_client()
        self.source = source  # 'local' ou 'cloud_actions'
        self.is_active = True
        self._last_command_check = None

    async def start(self) -> None:
        """Inicia as coroutines de heartbeat e listener de comandos em paralelo."""
        logger.info("🛰️ [CloudListener] Ativado. Heartbeat e controle remoto online.")
        await asyncio.gather(
            self._heartbeat_loop(),
            self._command_listener_loop(),
        )

    def stop(self) -> None:
        self.is_active = False

    # ── Heartbeat ──────────────────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Atualiza o heartbeat no Supabase a cada 60 segundos."""
        while self.is_active:
            try:
                self.db.table("system_heartbeat").upsert({
                    "source": self.source,
                    "worker_id": "ig-v2-01",
                    "worker_cycle": _current_cycle,
                    "status": "paused" if _is_paused else "ok",
                    "metadata": {
                        "pid": os.getpid(),
                        "platform": os.name,
                        "paused": _is_paused,
                    },
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }, on_conflict="source").execute()

                logger.debug(f"💓 [CloudListener] Heartbeat publicado (ciclo #{_current_cycle}).")
            except Exception as e:
                logger.error(f"❌ [CloudListener] Falha no heartbeat: {e}")

            await asyncio.sleep(60)

    # ── Command Listener ───────────────────────────────────────────────────────

    async def _command_listener_loop(self) -> None:
        """Verifica novos comandos pendentes no Supabase a cada 30 segundos."""
        while self.is_active:
            await asyncio.sleep(30)
            try:
                res = self.db.table("system_commands")\
                    .select("*")\
                    .eq("status", "pending")\
                    .order("issued_at", desc=False)\
                    .limit(5)\
                    .execute()

                for cmd in (res.data or []):
                    await self._execute_command(cmd)

            except Exception as e:
                logger.error(f"❌ [CloudListener] Erro ao verificar comandos: {e}")

    async def _execute_command(self, cmd: dict) -> None:
        """Executa um comando recebido do painel remoto."""
        global _is_paused, _restart_requested

        command = cmd.get("command", "").upper()
        cmd_id = cmd.get("id")
        logger.info(f"📡 [CloudListener] Comando recebido: {command} (ID: {cmd_id})")

        # Marca como em execução
        self.db.table("system_commands").update({
            "status": "executing",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", cmd_id).execute()

        result = "ok"
        try:
            if command == "PAUSE":
                _is_paused = True
                logger.warning("⏸️ [CloudListener] Sistema PAUSADO por comando remoto.")
                self._log_event("command_received", "Comando PAUSE executado.", {"command_id": cmd_id})

            elif command == "RESUME":
                _is_paused = False
                logger.info("▶️ [CloudListener] Sistema RETOMADO por comando remoto.")
                self._log_event("command_received", "Comando RESUME executado.", {"command_id": cmd_id})

            elif command == "RESTART":
                _restart_requested = True
                _is_paused = False
                logger.warning("🔄 [CloudListener] RESTART solicitado. O Watchdog reiniciará o runner.")
                self._log_event("command_received", "Comando RESTART sinalizado ao Watchdog.", {"command_id": cmd_id})
                # Levanta exceção para forçar saída do main_runner e acionar o Watchdog
                raise SystemExit("REMOTE_RESTART_REQUESTED")

            elif command == "UPDATE":
                logger.info("📥 [CloudListener] Executando git pull + reinstalação de dependências...")
                subprocess.run(["git", "pull"], check=False, timeout=60)
                subprocess.run(["uv", "pip", "install", "-r", "requirements-workers.txt", "-q"], check=False, timeout=120)
                _restart_requested = True
                self._log_event("command_received", "Comando UPDATE executado. Restart sinalizado.", {"command_id": cmd_id})

            elif command == "FORCE_SCRAPE":
                target = cmd.get("target")
                if target:
                    os.environ["TEST_TARGET_USERNAME"] = target
                    logger.info(f"🎯 [CloudListener] Alvo forçado definido: @{target}")
                    self._log_event("command_received", f"Alvo forçado: @{target}", {"command_id": cmd_id, "target": target})

            else:
                result = f"Comando desconhecido: {command}"
                logger.warning(f"⚠️ [CloudListener] {result}")

        except SystemExit:
            raise  # Re-lança para encerrar o processo
        except Exception as e:
            result = str(e)[:200]
            logger.error(f"💥 [CloudListener] Erro ao executar {command}: {e}")

        # Marca como concluído
        try:
            self.db.table("system_commands").update({
                "status": "done" if result == "ok" else "failed",
                "result": result,
            }).eq("id", cmd_id).execute()
        except Exception:
            pass

    def _log_event(self, event_type: str, description: str, metadata: dict = None) -> None:
        """Registra um evento de auditoria na tabela system_events."""
        try:
            self.db.table("system_events").insert({
                "event_type": event_type,
                "source": self.source,
                "severity": "info",
                "description": description,
                "metadata": metadata or {},
            }).execute()
        except Exception:
            pass


# Instância global
cloud_listener = CloudListener()
