#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agente Autônomo Sentinela v1.0 — Orquestrador Operacional Autónomo (YOLO/PASA v98.9)
Gerencia o ciclo completo de coleta de dados e inteligência de IA.
"""

from __future__ import annotations
import os
import sys
import argparse
import asyncio
import logging
import random
import requests
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from email.header import Header

# --- AUTO-ANCHORING ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

# Configuração mínima de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/sentinela_autonomous_agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("autonomous_agent")

from dotenv import load_dotenv

# --- Classes de Suporte ---

class NtfyNotifier:
    """Notificador especializado Ntfy com suporte UTF-8 MIME Header (PASA v98.9)."""
    def __init__(self, ntfy_url: Optional[str] = None, enabled: bool = True):
        self.enabled = enabled and (os.getenv("NTFY_ENABLED", "true").lower() == "true")
        
        if ntfy_url:
            self.ntfy_url = ntfy_url
        else:
            env_url = os.getenv("NTFY_URL", "https://ntfy.sh").rstrip("/")
            env_topic = os.getenv("NTFY_TOPIC", "sentinela")
            import urllib.parse
            parsed = urllib.parse.urlparse(env_url)
            if parsed.path.strip("/") != "":
                self.ntfy_url = env_url
            else:
                self.ntfy_url = f"{env_url}/{env_topic}"

    def notify(self, title: str, message: str, tags: str = "robot", priority: str = "default") -> bool:
        if not self.enabled:
            return False
        try:
            # Envio HTTP POST com headers MIME-encoded para aceitar emojis sem estourar latin-1
            headers = {
                "Title": Header(title, 'utf-8').encode(),
                "Tags": Header(tags, 'utf-8').encode(),
                "Priority": priority
            }
            response = requests.post(
                self.ntfy_url,
                data=message.encode('utf-8'),
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"⚠️ [Ntfy] Falha ao enviar notificação para {self.ntfy_url}: {e}")
            return False


class SupabaseHealthChecker:
    """Monitor de integridade de filas, sessões e recursos de banco de dados."""
    def __init__(self, db_client: Any):
        self.db = db_client

    async def check_health(self) -> Dict[str, Any]:
        health = {
            "status": "HEALTHY",
            "pending_count": 0,
            "locked_count": 0,
            "blocked_sessions_count": 0,
            "details": []
        }
        try:
            # 1. Consulta fila_coleta
            res = await asyncio.to_thread(
                self.db.table("fila_coleta").select("status,locked_by").execute
            )
            for item in res.data or []:
                if item["status"] == "PENDENTE":
                    health["pending_count"] += 1
                if item["locked_by"] is not None:
                    health["locked_count"] += 1

            if health["locked_count"] > 5:
                health["status"] = "DEGRADED"
                health["details"].append(f"Detectados {health['locked_count']} locks ativos na fila_coleta.")

            # 2. Consulta sessões do Instagram
            from core.instagram_scraper_v2 import InstagramScraperV2
            scraper = InstagramScraperV2()
            total_sessions = len(scraper.sessions)
            available_sessions = len([s for s in scraper.sessions if s.is_available])
            health["blocked_sessions_count"] = total_sessions - available_sessions

            if total_sessions > 0 and available_sessions == 0:
                health["status"] = "CRITICAL"
                health["details"].append("Zero sessões de Instagram disponíveis no pool.")
            elif available_sessions < (total_sessions * 0.5):
                if health["status"] != "CRITICAL":
                    health["status"] = "DEGRADED"
                health["details"].append(f"Mais de 50% das sessões bloqueadas ({health['blocked_sessions_count']}/{total_sessions}).")

        except Exception as e:
            health["status"] = "CRITICAL"
            health["details"].append(f"Erro ao acessar banco de dados Supabase: {e}")

        return health


class CollectorConfig:
    """Configurações operacionais do agente."""
    def __init__(self, **kwargs):
        self.max_posts = kwargs.get("max_posts", int(os.getenv("SENTINELA_MAX_POSTS", "3")))
        self.max_comments = kwargs.get("max_comments", int(os.getenv("SENTINELA_MAX_COMMENTS", "50")))
        self.max_age_days = kwargs.get("max_age_days", int(os.getenv("SENTINELA_MAX_AGE_DAYS", "7")))
        self.cycle_interval = kwargs.get("cycle_interval", int(os.getenv("CYCLE_INTERVAL", "60")))
        self.dry_run = kwargs.get("dry_run", os.getenv("DRY_RUN", "false").lower() == "true")
        self.ntfy_url = kwargs.get("ntfy_url", os.getenv("NTFY_URL"))

    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> CollectorConfig:
        if env_path and env_path.exists():
            load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=True)
        return cls()


class AutonomousCollector:
    """Coração do sistema: orquestrador autônomo de ciclos de processamento."""
    def __init__(self, config: CollectorConfig, db_client: Optional[Any] = None):
        self.config = config
        self.db = db_client
        self.notifier = NtfyNotifier(ntfy_url=config.ntfy_url)
        self.consecutive_blocks = 0
        self.cycle_count = 0

    async def run(
        self,
        worker_factory: Callable[[], Any],
        db_client: Any,
        max_cycles: Optional[int] = None
    ) -> None:
        """Loop principal de processamento autônomo."""
        self.db = db_client
        checker = SupabaseHealthChecker(db_client)
        from core.queue_manager import QueueManager
        queue_mgr = QueueManager(db_client)

        logger.info("🛰️ [Autopilot] Sentinela Autonomous Collector v1.0 Inicializado.")
        self.notifier.notify(
            "🛰️ Sentinela: Autopilot Iniciado",
            "Orquestrador Autônomo L4 operacional no workspace.",
            tags="satellite,robot",
            priority="high"
        )

        while max_cycles is None or self.cycle_count < max_cycles:
            self.cycle_count += 1
            start_time = datetime.now()
            logger.info(f"🔄 [Autopilot] Iniciando Ciclo #{self.cycle_count}...")

            # 1. Análise de Saúde (Diagnóstico)
            health = await checker.check_health()
            logger.info(f"📊 [Saúde] Status: {health['status']} | Locks: {health['locked_count']} | Pendentes: {health['pending_count']}")

            if health["status"] == "CRITICAL":
                warn_msg = f"Sistema em estado CRÍTICO!\nDetalhes: {', '.join(health['details'])}"
                logger.error(f"🚨 {warn_msg}")
                self.notifier.notify("🚨 Alerta Crítico: Saúde do Sistema", warn_msg, tags="warning,skull", priority="max")
                logger.info("⏸️ Aguardando cooldown de 5 minutos...")
                await asyncio.sleep(300)
                continue

            elif health["status"] == "DEGRADED":
                # Auto-recuperação de locks
                logger.warning("⚠️ [Autocura] Sistema degradado. Executando limpeza automática de locks...")
                unlocked = await queue_mgr.release_stale_locks(timeout_minutes=15)
                logger.info(f"🔓 [Autocura] {unlocked} locks órfãos liberados.")
                self.notifier.notify(
                    "⚠️ Alerta: Sistema Degradado",
                    f"Locks órfãos detectados e limpos automaticamente: {unlocked}.\nContinuando operação.",
                    tags="tools,warning",
                    priority="default"
                )

            # 2. Busca Próximo Alvo
            from core.queue_manager import Target
            target: Optional[Target] = None
            try:
                # Usa o fluxo oficial de extração de fila com lock
                target = await queue_mgr._get_from_fila_coleta(
                    blocked=set(),
                    seen_queue_ids=set(),
                    seen_targets=set(),
                    active_targets=set()
                )
            except Exception as e_queue:
                logger.error(f"❌ Erro ao consultar fila: {e_queue}")

            if not target:
                logger.info("😴 Fila de coleta vazia ou sem alvos prontos. Dormindo um ciclo...")
                await asyncio.sleep(self.config.cycle_interval)
                continue

            logger.info(f"🎯 [Alvo] Selecionado para raspagem: @{target.username} (Fila ID: {target.queue_id})")
            self.notifier.notify(
                f"🚀 Ciclo #{self.cycle_count} — @{target.username}",
                f"Iniciando coleta de comentários.\nFila ID: {target.queue_id}",
                tags="incoming_envelope,robot",
                priority="low"
            )

            # 3. Execução da Coleta
            extracted_count = 0
            inserted_count = 0
            duplicate_count = 0
            cycle_error = None
            
            try:
                if self.config.dry_run:
                    logger.info(f"[Dry-Run] Simulando raspagem de @{target.username}...")
                    await asyncio.sleep(2)
                    extracted_count = 10
                    inserted_count = 3
                    duplicate_count = 7
                else:
                    # Instancia worker real da fábrica
                    worker = worker_factory()
                    worker.db = self.db
                    worker.config.update({
                        "max_posts": self.config.max_posts,
                        "max_comments_per_post": self.config.max_comments,
                    })

                    # Callback incremental para sincronia direta
                    from core.local_buffer import SQLiteBuffer
                    buffer = SQLiteBuffer()

                    async def on_post_scraped(shortcode, comments):
                        # Envia dados no buffer para persistir Supabase
                        for c in comments:
                            buffer.add_comment(c)
                        sincronizados = buffer.sync_to_supabase()
                        logger.info(f"Sincronia Incremental: {sincronizados} novos comentários salvos.")

                    # Roda o scrape de perfil diretamente
                    from core.instagram_scraper_v2 import InstagramScraperV2
                    scraper = InstagramScraperV2(headless=worker.config.get("headless", True), db_client=self.db)
                    
                    res_scrape = await scraper.scrape_profile(
                        username=target.username,
                        candidato_id=target.username,
                        max_posts=self.config.max_posts,
                        max_comments_per_post=self.config.max_comments,
                        max_age_days=self.config.max_age_days,
                        on_post_scraped=on_post_scraped
                    )

                    # Força sincronização de restos
                    sincronizados_finais = buffer.sync_to_supabase()
                    
                    # Processa retorno
                    comments = res_scrape.get("comments", [])
                    extracted_count = len(comments)
                    inserted_count = sincronizados_finais
                    duplicate_count = max(0, extracted_count - inserted_count)
                    
                    self.consecutive_blocks = 0  # Sucesso zera contador de blocos

            except Exception as e_scrape:
                cycle_error = str(e_scrape)
                logger.error(f"💥 Falha no scraping do perfil @{target.username}: {e_scrape}")
                
                # Se detectou bloqueio/limites
                if "all_sessions_blocked" in cycle_error or "ExtractionFailure" in cycle_error:
                    self.consecutive_blocks += 1
                
                # Libera o alvo de forma segura (PATCH 4)
                target.error = "scrape_failed"

            # 4. Rotação do Alvo (Atualização de Frequência e liberação)
            try:
                await queue_mgr.rotate_target(target)
            except Exception as e_rot:
                logger.error(f"❌ Falha ao rotacionar alvo: {e_rot}")

            # 5. Execução do Ciclo de Classificação de IA (Se houveram novos inseridos)
            classified_count = 0
            if inserted_count > 0 or not self.config.dry_run:
                try:
                    from workers.processors.wk_classifica_comentarios import WkClassificaComentarios
                    ai_worker = WkClassificaComentarios(worker_id=f"auto-ai-{self.cycle_count}", config={})
                    ai_worker.db = self.db
                    
                    # Roda o ciclo de classificação
                    class_res = await ai_worker.run_cycle()
                    classified_count = class_res.get("classified", 0) if isinstance(class_res, dict) else 0
                    logger.info(f"🧠 [IA] Classificados {classified_count} comentários pendentes.")
                except Exception as e_ai:
                    logger.error(f"❌ Falha no ciclo de IA: {e_ai}")

            # 6. Relatório do Ciclo (Métricas detalhadas)
            duration = (datetime.now() - start_time).total_seconds()
            rate = (inserted_count / extracted_count * 100) if extracted_count > 0 else 0.0
            
            report_msg = (
                f"Duração: {duration:.1f}s\n"
                f"Posts: {self.config.max_posts}\n"
                f"Comentários: {extracted_count} extraídos | {inserted_count} novos | {duplicate_count} duplicados\n"
                f"Taxa de inserção: {rate:.1f}%\n"
                f"Classificados IA: {classified_count}\n"
            )
            if cycle_error:
                report_msg += f"⚠️ Erro: {cycle_error}\n"

            status_emoji = "❌" if cycle_error else "✅"
            self.notifier.notify(
                f"{status_emoji} Ciclo #{self.cycle_count} Concluído — @{target.username}",
                report_msg,
                tags="white_check_mark,robot" if not cycle_error else "x,warning",
                priority="default" if not cycle_error else "high"
            )

            # Decisão de Suspensão / Escalonamento (PAUSED)
            if self.consecutive_blocks >= 3:
                logger.critical("🛑 [Autopilot] 3 bloqueios seguidos detectados! Pausando orquestrador autônomo.")
                self.notifier.notify(
                    "🛑 Alerta: Orquestrador Suspenso",
                    "A execução automática foi suspensa após 3 falhas seguidas de extração/bloqueio. Requer intervenção de operador.",
                    tags="octagonal_sign,red_circle",
                    priority="max"
                )
                # Dorme por 30 minutos em modo de hibernação
                await asyncio.sleep(1800)
                self.consecutive_blocks = 0
                continue

            # Intervalo entre ciclos
            logger.info(f"😴 Dormindo por {self.config.cycle_interval}s antes do próximo ciclo...")
            await asyncio.sleep(self.config.cycle_interval)


# --- Modo Standalone (Execução CLI) ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinela Autonomous Collector v1.0")
    parser.add_argument("--dry-run", action="store_true", help="Executa em modo simulação (sem raspar de verdade)")
    parser.add_argument("--max-cycles", type=int, default=None, help="Número máximo de ciclos a executar")
    parser.add_argument("--env", type=str, default=".env", help="Caminho do arquivo .env")
    parser.add_argument("--interval", type=int, default=None, help="Intervalo em segundos entre ciclos")
    parser.add_argument("--ntfy-url", type=str, default=None, help="Tópico/URL do canal Ntfy")
    args = parser.parse_args()

    # Inicializa variáveis
    cfg = CollectorConfig.from_env(Path(args.env))
    if args.dry_run:
        cfg.dry_run = True
    if args.interval:
        cfg.cycle_interval = args.interval
    if args.ntfy_url:
        cfg.ntfy_url = args.ntfy_url

    from core.supabase_client import get_supabase_client
    from workers.scrapers.wk_coleta_instagram import WkColetaInstagram
    db = get_supabase_client()

    # Instancia e roda o orquestrador
    collector = AutonomousCollector(cfg)
    
    try:
        asyncio.run(
            collector.run(
                worker_factory=WkColetaInstagram,
                db_client=db,
                max_cycles=args.max_cycles
            )
        )
    except KeyboardInterrupt:
        logger.info("👋 Agente autônomo encerrado manualmente pelo operador.")
