
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGENTE AUTONOMO SENTINELA v1.0
Orquestrador Operacional de Coleta
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.exceptions import ExtractionFailure

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

def create_status_image(color: str) -> "Image.Image":
    """Gera uma imagem de circulo colorido em memoria para o status da bandeja."""
    if not TRAY_AVAILABLE:
        return None
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return image


# ============================================================
# [PATCH v1.0] GRACEFUL SHUTDOWN - Libera locks ao encerrar
# ============================================================
import signal
import atexit
import sys

_agent_instance = None  # Referencia ao agente para shutdown

def _register_agent_instance(agent):
    """Registra a instancia do agente para graceful shutdown."""
    global _agent_instance
    _agent_instance = agent

def _graceful_shutdown():
    """Libera locks e salva estado ao encerrar."""
    global _agent_instance
    if _agent_instance is not None:
        try:
            if hasattr(_agent_instance, "current_target") and _agent_instance.current_target:
                target = _agent_instance.current_target
                if hasattr(_agent_instance, "_smart_queue") and _agent_instance._smart_queue:
                    import asyncio
                    try:
                        # Executa a liberação de forma segura no loop de eventos ativo ou cria um loop temporário
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(_agent_instance._smart_queue.base_queue.release_atomic(
                                queue_id=target.id,
                                status="PENDENTE",
                                worker_id="sentinela_auto_worker"
                            ))
                        else:
                            loop.run_until_complete(_agent_instance._smart_queue.base_queue.release_atomic(
                                queue_id=target.id,
                                status="PENDENTE",
                                worker_id="sentinela_auto_worker"
                            ))
                    except Exception as e_loop:
                        print(f"[Shutdown] Erro ao obter loop: {e_loop}")
                print(f"[Shutdown] Lock liberado para @{target.username}")
            if hasattr(_agent_instance, "last_health") and hasattr(_agent_instance, "save_status"):
                _agent_instance.save_status(_agent_instance.last_health)
                print("[Shutdown] Status salvo em agent.status.json")
        except Exception as e:
            print(f"[Shutdown] Erro ao liberar lock: {e}")

def _signal_handler(signum, frame):
    """Handler para sinais de terminacao."""
    sig_name = {signal.SIGINT: "SIGINT (Ctrl+C)", signal.SIGTERM: "SIGTERM (kill)"}.get(signum, f"Signal {signum}")
    print(f"[Signal] Recebido {sig_name}, encerrando graciosamente...")
    _graceful_shutdown()
    sys.exit(0)

atexit.register(_graceful_shutdown)
try:
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
except (ValueError, OSError):
    pass
# ============================================================
# FIM DO PATCH GRACEFUL SHUTDOWN
# ============================================================


# =============================================================================
# CONFIGURACAO
# =============================================================================

@dataclass
class CollectorConfig:
    base_path: Path = field(default_factory=lambda: Path(r"C:\projetos\sentinela"))
    env_file: Path = field(default_factory=lambda: Path(r"C:\projetos\sentinela\.env"))
    max_posts: int = 10
    max_comments_per_post: int = 50
    max_age_days: int = 7
    high_activity_profiles: List[str] = field(default_factory=lambda: ["janjalula", "lulaoficial"])
    high_activity_max_posts: int = 20
    high_activity_max_comments: int = 100
    high_activity_max_age: int = 3
    min_insertion_rate_percent: float = 10.0
    max_consecutive_blocks: int = 3
    max_locks_orphaned: int = 5
    session_cooldown_seconds: int = 1800
    circuit_breaker_cooldown_seconds: int = 300
    cycle_interval_seconds: int = 60
    ntfy_url: str = "https://ntfy.sh/sentinela-monitor"
    ntfy_enabled: bool = True
    log_level: str = "INFO"
    log_file: Path = field(default_factory=lambda: Path("logs/autonomous_agent.log"))
    dry_run: bool = False
    max_cycles: int = 0

    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> "CollectorConfig":
        cfg = cls()
        if env_path and env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"\'')
        cfg.max_posts = int(os.getenv("SENTINELA_MAX_POSTS", cfg.max_posts))
        cfg.max_comments_per_post = int(os.getenv("SENTINELA_MAX_COMMENTS", cfg.max_comments_per_post))
        cfg.max_age_days = int(os.getenv("SENTINELA_MAX_AGE_DAYS", cfg.max_age_days))
        
        env_url = os.getenv("NTFY_URL")
        env_topic = os.getenv("NTFY_TOPIC")
        if env_url:
            env_url = env_url.rstrip("/")
            import urllib.parse
            parsed = urllib.parse.urlparse(env_url)
            if parsed.path.strip("/") != "":
                cfg.ntfy_url = env_url
            elif env_topic:
                cfg.ntfy_url = f"{env_url}/{env_topic}"
            else:
                cfg.ntfy_url = f"{env_url}/sentinela"
        
        cfg.ntfy_enabled = os.getenv("NTFY_ENABLED", "true").lower() == "true"
        cfg.log_level = os.getenv("LOG_LEVEL", cfg.log_level)
        cfg.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        cfg.cycle_interval_seconds = int(os.getenv("CYCLE_INTERVAL", cfg.cycle_interval_seconds))
        return cfg


# =============================================================================
# CLASSES DE ESTADO
# =============================================================================

@dataclass
class CycleMetrics:
    cycle_number: int = 0
    target_username: str = ""
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    posts_found: int = 0
    posts_processed: int = 0
    comments_extracted: int = 0
    comments_inserted: int = 0
    comments_duplicated: int = 0
    insertion_rate_percent: float = 0.0
    success: bool = False
    error: Optional[str] = None
    error_details: Optional[str] = None
    login_wall_detected: bool = False
    rate_limit_detected: bool = False
    dom_empty_detected: bool = False
    extraction_failure: bool = False
    session_rotated: bool = False
    lock_cleaned: bool = False
    dom_healing_triggered: bool = False
    circuit_breaker_opened: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle_number,
            "target": self.target_username,
            "duration_sec": round(self.duration_seconds, 2),
            "posts_found": self.posts_found,
            "posts_processed": self.posts_processed,
            "comments_extracted": self.comments_extracted,
            "comments_inserted": self.comments_inserted,
            "comments_duplicated": self.comments_duplicated,
            "insertion_rate_pct": round(self.insertion_rate_percent, 1),
            "success": self.success,
            "error": self.error,
            "login_wall": self.login_wall_detected,
            "rate_limit": self.rate_limit_detected,
            "dom_empty": self.dom_empty_detected,
            "extraction_failure": self.extraction_failure,
            "session_rotated": self.session_rotated,
            "lock_cleaned": self.lock_cleaned,
            "dom_healing": self.dom_healing_triggered,
            "circuit_open": self.circuit_breaker_opened,
        }


@dataclass
class SystemHealth:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    queue_total: int = 0
    queue_completed: int = 0
    queue_pending: int = 0
    queue_locked: int = 0
    queue_failed: int = 0
    locks_orphaned: int = 0
    sessions_total: int = 0
    sessions_available: int = 0
    sessions_blocked: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_service: str = ""
    consecutive_blocks: int = 0
    status: str = "HEALTHY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "queue": {
                "total": self.queue_total,
                "completed": self.queue_completed,
                "pending": self.queue_pending,
                "locked": self.queue_locked,
                "failed": self.queue_failed,
                "locks_orphaned": self.locks_orphaned,
            },
            "sessions": {
                "total": self.sessions_total,
                "available": self.sessions_available,
                "blocked": self.sessions_blocked,
            },
            "circuit_breaker": {
                "open": self.circuit_breaker_open,
                "service": self.circuit_breaker_service,
            },
            "consecutive_blocks": self.consecutive_blocks,
            "status": self.status,
        }


# =============================================================================
# NOTIFICADOR NTFY
# =============================================================================

class NtfyNotifier:
    def __init__(self, url: str, enabled: bool = True):
        self.url = url
        self.enabled = enabled
        self._last_notification_time: Optional[datetime] = None
        self._min_interval_seconds: int = 5

    async def send(self, title: str, message: str, priority: str = "default",
                   tags: Optional[List[str]] = None) -> bool:
        if not self.enabled:
            return True
        now = datetime.now(timezone.utc)
        if self._last_notification_time:
            elapsed = (now - self._last_notification_time).total_seconds()
            if elapsed < self._min_interval_seconds:
                await asyncio.sleep(self._min_interval_seconds - elapsed)
        try:
            import aiohttp
            headers = {"Title": title, "Priority": priority}
            if tags:
                headers["Tags"] = ",".join(tags)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, data=message.encode("utf-8")) as resp:
                    success = resp.status == 200
                    if success:
                        self._last_notification_time = datetime.now(timezone.utc)
                    return success
        except ImportError:
            try:
                import requests
                headers = {"Title": title, "Priority": priority}
                if tags:
                    headers["Tags"] = ",".join(tags)
                resp = requests.post(self.url, headers=headers, data=message.encode("utf-8"), timeout=10)
                success = resp.status_code == 200
                if success:
                    self._last_notification_time = datetime.now(timezone.utc)
                return success
            except Exception as e:
                logging.error(f"[Ntfy] Falha: {e}")
                return False
        except Exception as e:
            logging.error(f"[Ntfy] Falha: {e}")
            return False

    async def notify_cycle_start(self, cycle: int, target: str) -> bool:
        return await self.send(
            title=f"Ciclo #{cycle} — @{target}",
            message=f"Iniciando coleta de @{target}",
            priority="low",
            tags=["rocket"],
        )

    async def notify_cycle_complete(self, metrics: CycleMetrics) -> bool:
        emoji = "OK" if metrics.success else "ERRO"
        priority = "default" if metrics.success else "high"
        tags = ["white_check_mark"] if metrics.success else ["warning"]
        lines = [
            f"{emoji} Ciclo #{metrics.cycle_number} — @{metrics.target_username}",
            "",
            f"Duracao: {metrics.duration_seconds:.1f}s",
            f"Posts: {metrics.posts_processed}/{metrics.posts_found}",
            f"Comentarios: {metrics.comments_extracted} extraidos | {metrics.comments_inserted} novos | {metrics.comments_duplicated} duplicados",
            f"Taxa de insercao: {metrics.insertion_rate_percent:.1f}%",
        ]
        if metrics.error:
            lines.append(f"Erro: {metrics.error}")
        if metrics.login_wall_detected:
            lines.append("Login Wall detectado — sessao rotacionada")
        if metrics.rate_limit_detected:
            lines.append("Rate Limit — aguardando cooldown")
        if metrics.extraction_failure:
            lines.append("Falha estrutural — circuit breaker acionado")
        if metrics.dom_healing_triggered:
            lines.append("DOM Healing acionado")
        return await self.send(
            title=f"{emoji} Ciclo #{metrics.cycle_number} — @{metrics.target_username}",
            message="\n".join(lines),
            priority=priority,
            tags=tags,
        )

    async def notify_health_alert(self, health: SystemHealth) -> bool:
        emoji_map = {"HEALTHY": "OK", "DEGRADED": "ATENCAO", "CRITICAL": "CRITICO", "PAUSED": "PAUSA"}
        priority_map = {"HEALTHY": "low", "DEGRADED": "high", "CRITICAL": "urgent", "PAUSED": "default"}
        emoji = emoji_map.get(health.status, "?")
        priority = priority_map.get(health.status, "default")
        lines = [
            f"{emoji} Estado: {health.status}",
            "",
            f"Fila: {health.queue_total} total | {health.queue_pending} pendentes | {health.queue_locked} em curso | {health.queue_failed} falhas",
            f"Locks orfaos: {health.locks_orphaned}",
            f"Sessoes: {health.sessions_available}/{health.sessions_total} disponiveis",
        ]
        if health.circuit_breaker_open:
            lines.append(f"Circuit Breaker ABERTO para {health.circuit_breaker_service}")
        return await self.send(
            title=f"Sentinela — {health.status}",
            message="\n".join(lines),
            priority=priority,
            tags=["heartbeat"],
        )


# =============================================================================
# VERIFICADOR DE SAUDE SUPABASE
# =============================================================================

class SupabaseHealthChecker:
    def __init__(self, db_client):
        self.db = db_client

    async def check_queue_health(self) -> Dict[str, int]:
        try:
            import asyncio
            result = await asyncio.to_thread(
                self.db.table("fila_coleta").select("status,locked_by", count="exact").execute
            )
            data = result.data if hasattr(result, "data") else []
            stats = {"total": 0, "completed": 0, "pending": 0, "locked": 0, "failed": 0, "orphaned": 0}
            for row in data:
                stats["total"] += 1
                status = row.get("status", "")
                if status == "CONCLUIDO":
                    stats["completed"] += 1
                elif status == "EM_CURSO":
                    stats["locked"] += 1
                    locked_at = row.get("locked_at")
                    if locked_at:
                        try:
                            lock_time = datetime.fromisoformat(locked_at.replace("Z", "+00:00"))
                            if datetime.now(timezone.utc) - lock_time > timedelta(minutes=30):
                                stats["orphaned"] += 1
                        except:
                            pass
                elif status in ("FALHADO", "ERRO"):
                    stats["failed"] += 1
                else:
                    stats["pending"] += 1
            return stats
        except Exception as e:
            logging.error(f"[HealthChecker] Falha ao verificar fila: {e}")
            return {"total": 0, "completed": 0, "pending": 0, "locked": 0, "failed": 0, "orphaned": 0}

    async def check_sessions(self, session_pool) -> Dict[str, int]:
        try:
            sessions = []
            if hasattr(session_pool, "_sessions"):
                sessions = session_pool._sessions
            elif hasattr(session_pool, "sessions"):
                sessions = session_pool.sessions
            elif isinstance(session_pool, list):
                sessions = session_pool
                
            total = len(sessions)
            available = sum(1 for s in sessions if getattr(s, "is_available", True))
            blocked = total - available
            return {"total": total, "available": available, "blocked": blocked}
        except Exception as e:
            logging.error(f"[HealthChecker] Falha ao verificar sessoes: {e}")
            return {"total": 0, "available": 0, "blocked": 0}

    async def release_orphaned_locks(self) -> int:
        try:
            import asyncio
            result = await asyncio.to_thread(
                self.db.rpc("fila_coleta_release_stale", {"stale_minutes": 30}).execute
            )
            return getattr(result, "count", 0) or 0
        except Exception as e:
            logging.error(f"[HealthChecker] Falha ao liberar locks: {e}")
            return 0




# =============================================================================
# CONTROLE DE FLUXO DA FILA v1.1
# =============================================================================

@dataclass
class TargetState:
    """Estado de processamento de um alvo específico."""
    username: str
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_processed: Optional[datetime] = None
    cycles_attempted: int = 0
    cycles_successful: int = 0
    cycles_empty: int = 0  # Ciclos onde 0 comentários novos foram inseridos
    total_comments_inserted: int = 0
    consecutive_empty_cycles: int = 0
    status: str = "ACTIVE"  # ACTIVE, BACKOFF, EXHAUSTED, BLOCKED
    backoff_until: Optional[datetime] = None
    last_error: Optional[str] = None

    def record_cycle(self, metrics: CycleMetrics):
        self.cycles_attempted += 1
        self.last_processed = datetime.now(timezone.utc)

        if metrics.success and metrics.comments_inserted > 0:
            self.cycles_successful += 1
            self.total_comments_inserted += metrics.comments_inserted
            self.consecutive_empty_cycles = 0
            self.status = "ACTIVE"
        elif metrics.success and metrics.comments_inserted == 0:
            self.cycles_empty += 1
            self.consecutive_empty_cycles += 1
            # Se 3+ ciclos vazios consecutivos, considera alvo esgotado temporariamente
            if self.consecutive_empty_cycles >= 3:
                self.status = "EXHAUSTED"
                self.backoff_until = datetime.now(timezone.utc) + timedelta(hours=2)
        else:
            # Falha
            self.last_error = metrics.error
            self.consecutive_empty_cycles += 1
            if metrics.login_wall_detected or metrics.rate_limit_detected:
                self.status = "BLOCKED"
                self.backoff_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            elif metrics.extraction_failure:
                self.status = "BACKOFF"
                self.backoff_until = datetime.now(timezone.utc) + timedelta(minutes=15)

    def can_process(self) -> bool:
        if self.status in ("EXHAUSTED", "BLOCKED", "BACKOFF"):
            if self.backoff_until and datetime.now(timezone.utc) < self.backoff_until:
                return False
            # Backoff expirou, volta para ACTIVE
            self.status = "ACTIVE"
            self.consecutive_empty_cycles = 0
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "status": self.status,
            "cycles_attempted": self.cycles_attempted,
            "cycles_successful": self.cycles_successful,
            "cycles_empty": self.cycles_empty,
            "consecutive_empty": self.consecutive_empty_cycles,
            "total_inserted": self.total_comments_inserted,
            "last_processed": self.last_processed.isoformat() if self.last_processed else None,
            "backoff_until": self.backoff_until.isoformat() if self.backoff_until else None,
            "last_error": self.last_error,
        }


class SmartQueueManager:
    """Gerenciador inteligente de fila com controle de fluxo e backoff."""

    def __init__(self, base_queue_manager, config: CollectorConfig, worker_id: str = "sentinela_auto_worker"):
        self.base_queue = base_queue_manager
        self.cfg = config
        self.worker_id = worker_id
        self.target_states: Dict[str, TargetState] = {}
        self.global_empty_cycles = 0
        self.last_successful_insertion: Optional[datetime] = None

    def get_or_create_state(self, username: str) -> TargetState:
        if username not in self.target_states:
            self.target_states[username] = TargetState(username=username)
        return self.target_states[username]

    async def claim_next_target_smart(self) -> Optional[Any]:
        """Pega próximo alvo da fila, respeitando backoff e estado."""
        max_attempts = 5
        for attempt in range(max_attempts):
            target = await self.base_queue.claim_next_target_atomic(self.worker_id)
            if not target:
                return None

            state = self.get_or_create_state(target.username)

            if state.can_process():
                return target
            else:
                # Alvo em backoff, libera e pega próximo
                await self.base_queue.release_atomic(
                    target.queue_id, 
                    "PENDENTE", 
                    self.worker_id
                )
                continue

        return None

    def record_cycle_result(self, username: str, metrics: CycleMetrics):
        """Registra resultado do ciclo no estado do alvo."""
        state = self.get_or_create_state(username)
        state.record_cycle(metrics)

        if metrics.comments_inserted > 0:
            self.last_successful_insertion = datetime.now(timezone.utc)
            self.global_empty_cycles = 0
        else:
            self.global_empty_cycles += 1

    def should_pause_globally(self) -> Tuple[bool, str]:
        """Determina se o sistema inteiro deve pausar por falta de atividade."""
        # Se 10+ ciclos globais vazios, sugere pausa longa
        if self.global_empty_cycles >= 10:
            return True, f"{self.global_empty_cycles} ciclos globais sem insercoes. Possivel bloqueio massivo."

        # Se todos os alvos conhecidos estão em backoff/exhausted
        if self.target_states:
            all_blocked = all(s.status in ("EXHAUSTED", "BLOCKED", "BACKOFF") for s in self.target_states.values())
            if all_blocked:
                return True, "Todos os alvos em backoff. Aguardando recuperacao."

        return False, ""

    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas do gerenciador inteligente."""
        statuses = {}
        for state in self.target_states.values():
            statuses[state.status] = statuses.get(state.status, 0) + 1

        return {
            "targets_tracked": len(self.target_states),
            "status_distribution": statuses,
            "global_empty_cycles": self.global_empty_cycles,
            "last_successful_insertion": self.last_successful_insertion.isoformat() if self.last_successful_insertion else None,
        }

# =============================================================================
# ORQUESTRADOR AUTONOMO
# =============================================================================

class AutonomousCollector:
    """Agente autonomo que gerencia o ciclo completo de coleta."""

    def __init__(self, config: Optional[CollectorConfig] = None):
        # [PATCH] Registrar instancia para graceful shutdown
        _register_agent_instance(self)
        self.cfg = config or CollectorConfig.from_env()
        self.ntfy = NtfyNotifier(self.cfg.ntfy_url, self.cfg.ntfy_enabled)
        self.health_checker: Optional[SupabaseHealthChecker] = None
        self.cycle_count = 0
        self.consecutive_blocks = 0
        self.is_running = False
        self.is_paused = False
        self.tray_icon = None
        self.tray_thread = None
        self.last_health = None
        self._setup_logging()

    def save_status(self, health: Optional[SystemHealth] = None):
        try:
            pending_count = health.queue_pending if health else 0
            status_data = {
                "cycle_count": self.cycle_count,
                "status": health.status if health else "RUNNING",
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "pending_queue": pending_count,
                "consecutive_blocks": self.consecutive_blocks,
                "sessions": {
                    "available": health.sessions_available if health else 0,
                    "blocked": health.sessions_blocked if health else 0,
                    "total": health.sessions_total if health else 0
                } if health else {}
            }
            if hasattr(self, '_smart_queue'):
                status_data["smart_queue"] = self._smart_queue.get_stats()
                
            # Escreve o heartbeat persistente
            Path("agent.status.json").write_text(json.dumps(status_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            self.logger.debug(f"[Agent] Erro ao salvar status: {e}")

    def _setup_logging(self):
        level = getattr(logging, self.cfg.log_level.upper(), logging.INFO)
        self.cfg.log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(self.cfg.log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger("AutonomousCollector")

    def _get_limits_for_target(self, username: str) -> Tuple[int, int, int]:
        """Retorna (max_posts, max_comments, max_age_days) conforme perfil."""
        if username.lower() in [p.lower() for p in self.cfg.high_activity_profiles]:
            return (
                self.cfg.high_activity_max_posts,
                self.cfg.high_activity_max_comments,
                self.cfg.high_activity_max_age,
            )
        return self.cfg.max_posts, self.cfg.max_comments_per_post, self.cfg.max_age_days

    async def check_system_health(self, db_client, session_pool) -> SystemHealth:
        """Verifica saude geral do sistema e toma acoes corretivas."""
        health = SystemHealth()
        self.health_checker = SupabaseHealthChecker(db_client)

        # Verifica fila
        queue_stats = await self.health_checker.check_queue_health()
        health.queue_total = queue_stats["total"]
        health.queue_completed = queue_stats["completed"]
        health.queue_pending = queue_stats["pending"]
        health.queue_locked = queue_stats["locked"]
        health.queue_failed = queue_stats["failed"]
        health.locks_orphaned = queue_stats["orphaned"]

        # Libera locks orfaos se necessario
        if health.locks_orphaned > self.cfg.max_locks_orphaned:
            self.logger.warning(f"[Health] {health.locks_orphaned} locks orfaos detectados. Liberando...")
            released = await self.health_checker.release_orphaned_locks()
            self.logger.info(f"[Health] {released} locks liberados.")
            health.lock_cleaned = True
            health.locks_orphaned = max(0, health.locks_orphaned - released)

        # Verifica sessoes
        session_stats = await self.health_checker.check_sessions(session_pool)
        health.sessions_total = session_stats["total"]
        health.sessions_available = session_stats["available"]
        health.sessions_blocked = session_stats["blocked"]

        # Verifica circuit breaker (se disponivel)
        try:
            from core.circuit_breaker import scraper_circuit_breaker
            health.circuit_breaker_open = not scraper_circuit_breaker.can_execute("instagram")
            health.circuit_breaker_service = "instagram"
        except:
            pass

        # Determina status
        health.consecutive_blocks = self.consecutive_blocks
        if self.consecutive_blocks >= self.cfg.max_consecutive_blocks:
            health.status = "PAUSED"
        elif health.circuit_breaker_open or health.sessions_available == 0:
            health.status = "CRITICAL"
        elif health.locks_orphaned > 0 or health.sessions_blocked > health.sessions_available:
            health.status = "DEGRADED"
        else:
            health.status = "HEALTHY"

        return health

    async def execute_collection_cycle(self, worker, target) -> CycleMetrics:
        """Executa um ciclo de coleta com monitoramento completo."""
        metrics = CycleMetrics()
        metrics.cycle_number = self.cycle_count
        metrics.target_username = target.username
        metrics.start_time = datetime.now(timezone.utc)

        self.logger.info(f"[Cycle #{self.cycle_count}] Iniciando coleta de @{target.username}")
        await self.ntfy.notify_cycle_start(self.cycle_count, target.username)

        try:
            # Obtem limites para o alvo
            max_posts, max_comments, max_age = self._get_limits_for_target(target.username)
            self.logger.info(f"[Cycle #{self.cycle_count}] Limites: posts={max_posts}, comments={max_comments}, age={max_age}d")

            # Executa coleta
            if self.cfg.dry_run:
                self.logger.info("[Cycle] MODO DRY-RUN: simulando coleta")
                result = type("obj", (object,), {
                    "success": True,
                    "comments": [],
                    "post_metas": [],
                    "comments_collected": 0,
                    "posts_processed": 0,
                })()
            else:
                # Configura limites no worker
                worker.max_posts = max_posts
                worker.max_comments_per_post = max_comments
                worker.max_age_days = max_age
                result = await worker.run_cycle()

            # Processa resultado
            metrics.end_time = datetime.now(timezone.utc)
            metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()

            # Verifica sucesso (se tiver flag de sucesso ou se nao houver erros)
            is_success = False
            if hasattr(result, "success") and result.success:
                is_success = True
            elif hasattr(result, "db_success") and result.db_success:
                is_success = True
            elif result and getattr(result, "error", None) is None:
                is_success = True

            if is_success:
                metrics.success = True
                metrics.comments_extracted = getattr(result, "extracted", 0)
                metrics.comments_inserted = getattr(result, "inserted", 0)
                metrics.comments_duplicated = getattr(result, "duplicated", 0)
                metrics.posts_processed = getattr(result, "posts_processed", 0)

                # Calcula taxa de insercao
                if metrics.comments_extracted > 0:
                    metrics.insertion_rate_percent = (metrics.comments_inserted / metrics.comments_extracted) * 100

                self.logger.info(f"[Cycle #{self.cycle_count}] Sucesso: {metrics.comments_inserted} novos comentarios inseridos")
                self.consecutive_blocks = 0  # Reseta contador de blocos

            else:
                # Falha
                metrics.success = False
                metrics.error = getattr(result, "error", "unknown_error")
                
                # Apenas incrementa consecutive_blocks se for um erro de bloqueio/falha real de infraestrutura
                # Erros legítimos como "no_posts_found" não devem travar o sistema inteiro
                is_infra_error = True
                if metrics.error in ("no_posts_found", "no_new_comments"):
                    is_infra_error = False
                    
                if is_infra_error:
                    self.consecutive_blocks += 1
                    self.logger.warning(f"[Cycle #{self.cycle_count}] Falha de infraestrutura: {metrics.error} (Blocos: {self.consecutive_blocks})")
                else:
                    self.logger.info(f"[Cycle #{self.cycle_count}] Alvo sem novos dados (legitimo): {metrics.error}")
                    # Reseta consecutive_blocks pois o sistema está operando normalmente
                    self.consecutive_blocks = 0

                # Detecta tipo de falha
                if "extraction_failure" in str(metrics.error).lower():
                    metrics.extraction_failure = True
                elif "login" in str(metrics.error).lower() or "auth" in str(metrics.error).lower():
                    metrics.login_wall_detected = True
                elif "rate" in str(metrics.error).lower() or "429" in str(metrics.error):
                    metrics.rate_limit_detected = True
                elif "dom" in str(metrics.error).lower() or "empty" in str(metrics.error).lower():
                    metrics.dom_empty_detected = True

        except ExtractionFailure as ef:
            metrics.end_time = datetime.now(timezone.utc)
            metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.success = False
            metrics.error = "ExtractionFailure"
            metrics.error_details = str(ef)
            self.consecutive_blocks += 1
            self.logger.error(f"[Cycle #{self.cycle_count}] Falha na extração de dados (ExtractionFailure): {ef}")
        except Exception as e:
            metrics.end_time = datetime.now(timezone.utc)
            metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.success = False
            metrics.error = type(e).__name__
            metrics.error_details = str(e)
            self.consecutive_blocks += 1
            self.logger.error(f"[Cycle #{self.cycle_count}] Exceção: {e}")
            self.logger.error(traceback.format_exc())

        # Notifica resultado
        await self.ntfy.notify_cycle_complete(metrics)
        return metrics

    async def run(self, worker_factory=None, db_client=None, session_pool=None):
        """Loop principal do agente autonomo."""
        self.is_running = True
        self.current_target = None
        self.logger.info("=" * 60)
        self.logger.info("AGENTE AUTONOMO SENTINELA v1.0 — Iniciando operacao")
        self.logger.info("=" * 60)
        self.logger.info(f"Modo: {'DRY-RUN' if self.cfg.dry_run else 'PRODUCAO'}")
        self.logger.info(f"Intervalo entre ciclos: {self.cfg.cycle_interval_seconds}s")
        self.logger.info(f"Max ciclos: {self.cfg.max_cycles or 'infinito'}")

        # Inicializa o icone na system tray se disponivel
        self.start_tray_icon()

        try:
            while self.is_running:
                if self.is_paused:
                    self.logger.info("[Agent] Operacao pausada via bandeja do sistema. Aguardando...")
                    await asyncio.sleep(5)
                    continue

                self.cycle_count += 1

                # Verifica saude do sistema
                if db_client and session_pool:
                    health = await self.check_system_health(db_client, session_pool)
                    self.last_health = health
                    self.save_status(health)

                    # Alerta de fila baixa
                    if health.queue_pending < 10:
                        try:
                            await self.ntfy.send(
                                title="Sentinela — Fila Baixa",
                                message=f"Apenas {health.queue_pending} alvos pendentes na fila. Verifique candidatos ATIVOS.",
                                priority="high",
                                tags=["warning", "inbox_tray"]
                            )
                        except Exception as e_ntfy:
                            self.logger.debug(f"Falha ao enviar alerta de fila baixa: {e_ntfy}")

                    # Log de estatísticas do SmartQueueManager a cada 5 ciclos
                    if self.cycle_count % 5 == 0 and hasattr(self, '_smart_queue'):
                        sq_stats = self._smart_queue.get_stats()
                        self.logger.info(f"[SmartQueue] {sq_stats}")
                    self.logger.info(f"[Health] Status: {health.status} | Fila: {health.queue_pending} pendentes | Sessoes: {health.sessions_available}/{health.sessions_total}")

                    if health.status == "PAUSED":
                        self.logger.warning(f"[Health] Sistema PAUSADO por {self.cfg.max_consecutive_blocks} blocos consecutivos. Aguardando {self.cfg.cycle_interval_seconds * 2}s...")
                        await self.ntfy.notify_health_alert(health)
                        await asyncio.sleep(self.cfg.cycle_interval_seconds * 2)
                        continue

                    if health.status == "CRITICAL":
                        self.logger.error("[Health] Sistema em estado CRITICO. Aguardando recuperacao...")
                        await self.ntfy.notify_health_alert(health)
                        await asyncio.sleep(self.cfg.circuit_breaker_cooldown_seconds)
                        continue

                    if health.status == "DEGRADED":
                        self.logger.warning("[Health] Sistema DEGRADADO. Continuando com cautela...")
                        await self.ntfy.notify_health_alert(health)

                # Obtem proximo alvo da fila (com controle inteligente)
                if worker_factory:
                    worker = worker_factory()

                    # Inicializa SmartQueueManager se ainda nao existir
                    if not hasattr(self, '_smart_queue'):
                        self._smart_queue = SmartQueueManager(worker.queue, self.cfg, worker.worker_id)

                    # Garante que a fila esteja populada
                    try:
                        await self._smart_queue.base_queue._ensure_queue_populated()
                    except Exception as e_repop:
                        self.logger.warning(f"[Queue] Erro ao auto-repopular fila: {e_repop}")

                    # Verifica pausa global
                    should_pause, pause_reason = self._smart_queue.should_pause_globally()
                    if should_pause:
                        self.logger.warning(f"[SmartQueue] PAUSA GLOBAL: {pause_reason}")
                        await self.ntfy.send(
                            title="Sentinela — Pausa Global",
                            message=f"Sistema pausado: {pause_reason}",
                            priority="high",
                            tags=["pause_button"],
                        )
                        
                        # Recuperação inteligente de pausa global (v1.2)
                        self.logger.info("[PauseRecovery] Iniciando pausa global. Verificando a cada 30s...")
                        pause_start = datetime.now(timezone.utc)
                        recovery_timeout = timedelta(hours=1)
                        retomado = False
                        
                        while not retomado:
                            now = datetime.now(timezone.utc)
                            # 1. Timeout máximo de 1 hora
                            if (now - pause_start) > recovery_timeout:
                                self.logger.warning("[PauseRecovery] Timeout de 1h atingido. Forçando retomada...")
                                for state in self._smart_queue.target_states.values():
                                    state.status = "ACTIVE"
                                    state.backoff_until = None
                                    state.consecutive_empty_cycles = 0
                                self._smart_queue.global_empty_cycles = 0
                                
                                await self.ntfy.send(
                                    title="Sentinela — Timeout de Pausa",
                                    message="Timeout de pausa atingido (1h). Forçando retomada e limpando cooldowns.",
                                    priority="high",
                                    tags=["alarm_clock"]
                                )
                                retomado = True
                                break
                            
                            # 2. Verifica se algum alvo voltou para ACTIVE
                            ativos = 0
                            for state in self._smart_queue.target_states.values():
                                if state.can_process():
                                    ativos += 1
                                    
                            # 3. Verifica se tem algum item novo PENDENTE na fila do Supabase
                            pending_in_db = 0
                            try:
                                if db_client:
                                    res_pending = await asyncio.to_thread(
                                        db_client.table("fila_coleta")
                                        .select("id", count="exact")
                                        .eq("status", "PENDENTE")
                                        .execute
                                    )
                                    pending_in_db = res_pending.count or 0
                            except Exception as e_pending:
                                self.logger.debug(f"[PauseRecovery] Falha ao verificar fila: {e_pending}")
                                
                            self.logger.info(
                                f"[PauseRecovery] Verificação: {ativos} alvos ACTIVE | {pending_in_db} pendentes na fila"
                            )
                            
                            if ativos > 0 or pending_in_db > 0:
                                self.logger.info(f"[PauseRecovery] RETOMANDO! {ativos} alvos prontos, {pending_in_db} pendentes.")
                                await self.ntfy.send(
                                    title="Sentinela — Retomada",
                                    message=f"Sistema retomado. Alvos ativos={ativos}, pendentes={pending_in_db}.",
                                    priority="default",
                                    tags=["play_button"]
                                )
                                self._smart_queue.global_empty_cycles = 0
                                retomado = True
                                break
                                
                            await asyncio.sleep(30)
                        continue

                    target = await self._smart_queue.claim_next_target_smart()

                    if not target:
                        self.logger.info("[Cycle] Nenhum alvo disponivel na fila. Aguardando...")
                        await asyncio.sleep(self.cfg.cycle_interval_seconds)
                        continue

                    # Salva alvo ativo para SRE Graceful Shutdown
                    self.current_target = target

                    # Executa ciclo de coleta
                    metrics = await self.execute_collection_cycle(worker, target)

                    # Registra resultado no controle inteligente de fluxo
                    self._smart_queue.record_cycle_result(target.username, metrics)
                    self.logger.info(f"[Cycle #{self.cycle_count}] Finalizado em {metrics.duration_seconds:.1f}s | Status: {'OK' if metrics.success else 'FALHA'}")
                    
                    # Limpa alvo ativo
                    self.current_target = None
                else:
                    self.logger.warning("[Cycle] worker_factory nao fornecido. Modo monitoramento apenas.")
                    await asyncio.sleep(self.cfg.cycle_interval_seconds)

                # Verifica limite de ciclos
                if self.cfg.max_cycles > 0 and self.cycle_count >= self.cfg.max_cycles:
                    self.logger.info(f"[Cycle] Limite de {self.cfg.max_cycles} ciclos atingido. Encerrando.")
                    break

                # Intervalo entre ciclos
                await asyncio.sleep(self.cfg.cycle_interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("[Agent] Interrompido pelo usuario.")
        except Exception as e:
            self.logger.error(f"[Agent] Erro fatal: {e}")
            self.logger.error(traceback.format_exc())
            await self.ntfy.send(
                title="Sentinela — ERRO FATAL",
                message=f"Agente autonomo encerrou com erro: {e}",
                priority="urgent",
                tags=["skull"],
            )
        finally:
            self.is_running = False
            self.logger.info("[Agent] Agente autonomo finalizado.")

    def stop(self):
        self.is_running = False
        self.logger.info("[Agent] Sinal de parada recebido.")
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass

    def start_tray_icon(self):
        """Inicializa e executa o icone de bandeja em thread dedicada."""
        if not TRAY_AVAILABLE:
            self.logger.warning("[Tray] pystray ou PIL nao disponiveis. Ignorando tray icon.")
            return

        try:
            self.logger.info("[Tray] Inicializando icone na bandeja...")
            icon_image = create_status_image("#4CAF50") # Verde inicial

            menu = pystray.Menu(
                pystray.MenuItem("Status", self._on_tray_status),
                pystray.MenuItem("Pausar/Retomar", self._on_tray_toggle_pause),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Parar", self._on_tray_stop),
                pystray.MenuItem("Sair (Remover Icone)", self._on_tray_exit)
            )

            self.tray_icon = pystray.Icon(
                "sentinela_agent",
                icon_image,
                title="Sentinela — Inicializando",
                menu=menu
            )

            import threading
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()

            # Thread para atualizar periodicamente o tooltip e a cor do icone
            threading.Thread(target=self._update_tray_loop, daemon=True).start()

        except Exception as e:
            self.logger.error(f"[Tray] Falha ao iniciar tray icon: {e}")

    def _on_tray_status(self, icon, item):
        status_msg = (
            f"Sentinela v1.2\n"
            f"Status: {'Pausado' if self.is_paused else 'Rodando'}\n"
            f"Ciclos: {self.cycle_count}\n"
            f"Blocos consecutivos: {self.consecutive_blocks}\n"
            f"Alvos: {len(self._smart_queue.target_states) if hasattr(self, '_smart_queue') else 0} rastreados"
        )
        icon.notify(status_msg, title="Sentinela — Status")

    def _on_tray_toggle_pause(self, icon, item):
        self.is_paused = not self.is_paused
        status = "Pausado" if self.is_paused else "Retomado"
        self.logger.info(f"[Tray] Agente {status} via menu tray.")
        icon.notify(f"Agente {status} com sucesso.", title="Sentinela")

    def _on_tray_stop(self, icon, item):
        self.logger.info("[Tray] Parando agente via menu tray.")
        self.stop()
        icon.notify("Parando agente de forma amigavel...", title="Sentinela")

    def _on_tray_exit(self, icon, item):
        self.logger.info("[Tray] Removendo icone da bandeja.")
        icon.stop()
        self.tray_icon = None

    def _update_tray_loop(self):
        while self.is_running and self.tray_icon:
            try:
                # Cores e textos conforme estado
                color = "#4CAF50" # Verde (HEALTHY / RUNNING)
                title = f"Sentinela — Rodando | Ciclo #{self.cycle_count}"

                if self.is_paused:
                    color = "#FFC107" # Amarelo (PAUSED)
                    title = "Sentinela — Pausado"
                elif self.last_health and self.last_health.queue_pending == 0:
                    color = "#2196F3" # Azul (IDLE)
                    title = "Sentinela — Sem alvos pendentes (IDLE)"
                elif self.consecutive_blocks >= self.cfg.max_consecutive_blocks:
                    color = "#F44336" # Vermelho (BLOCKED)
                    title = "Sentinela — Bloqueado/Suspenso"
                elif hasattr(self, '_smart_queue'):
                    stats = self._smart_queue.get_stats()
                    if stats.get("global_empty_cycles", 0) >= 5:
                        color = "#FFC107" # Amarelo (DEGRADED)
                        title = "Sentinela — Sem atividade recente"

                self.tray_icon.icon = create_status_image(color)
                self.tray_icon.title = title
            except Exception as e:
                self.logger.debug(f"[Tray] Erro ao atualizar icone: {e}")
            time.sleep(5)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Agente Autonomo Sentinela v1.0 — Orquestrador de Coleta",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exemplos:\n  python sentinela_autonomous_agent.py\n  python sentinela_autonomous_agent.py --env .env.producao --dry-run\n  python sentinela_autonomous_agent.py --max-cycles 10",
    )
    parser.add_argument("--env", help="Caminho do arquivo .env")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulacao (nao coleta)")
    parser.add_argument("--max-cycles", type=int, default=0, help="Maximo de ciclos (0=infinito)")
    parser.add_argument("--interval", type=int, help="Intervalo entre ciclos em segundos")
    parser.add_argument("--ntfy-url", help="URL do topico Ntfy")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    # Carrega configuracao
    env_path = Path(args.env) if args.env else None
    cfg = CollectorConfig.from_env(env_path)

    if args.dry_run:
        cfg.dry_run = True
    if args.max_cycles:
        cfg.max_cycles = args.max_cycles
    if args.interval:
        cfg.cycle_interval_seconds = args.interval
    if args.ntfy_url:
        cfg.ntfy_url = args.ntfy_url
    cfg.log_level = args.log_level

    # Inicializa dependencias se as libs do projeto estiverem disponiveis
    worker_factory = None
    db_client = None
    session_pool = None

    try:
        from core.supabase_client import get_supabase_client
        from workers.scrapers.wk_coleta_instagram import WkColetaInstagram
        from core.instagram_scraper_v2 import InstagramScraperV2

        db_client = get_supabase_client()
        
        worker_config = {
            "headless": True,
            "max_retries": 3,
            "max_posts": cfg.max_posts,
            "max_comments": cfg.max_comments_per_post,
            "max_age_days": cfg.max_age_days
        }
        worker_factory = lambda: WkColetaInstagram(worker_id="sentinela_auto_worker", config=worker_config)
        
        scraper = InstagramScraperV2()
        session_pool = scraper.sessions
    except Exception as e_deps:
        print(f"⚠️ [Deps] Nao foi possivel carregar as dependencias completas do projeto: {e_deps}")
        print("Executando em modo monitoramento de fila basico...")

    # Cria e executa agente
    agent = AutonomousCollector(cfg)

    try:
        asyncio.run(agent.run(
            worker_factory=worker_factory,
            db_client=db_client,
            session_pool=session_pool
        ))
    except KeyboardInterrupt:
        agent.stop()
        print("\nAgente interrompido.")


if __name__ == "__main__":
    main()
