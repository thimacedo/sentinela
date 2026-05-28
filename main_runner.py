from __future__ import annotations
import os
import sys

# --- AUTO-ANCHORING (v61.6) ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import asyncio
import logging
import signal

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass


from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)

# Configuração de Logging v50.1-final
os.makedirs("logs", exist_ok=True)
WATCHDOG_ACTIVE = os.getenv("WATCHDOG_ACTIVE") == "true"

root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING) # Modo Quiet por padrão (v84.13)
root_logger.handlers.clear()

console_handler = logging.StreamHandler(sys.stdout)
if WATCHDOG_ACTIVE:
    console_format = "%(message)s"
else:
    console_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
console_handler.setFormatter(logging.Formatter(console_format))

from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler("logs/main_runner.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Habilitar INFO apenas para os logs operacionais essenciais
for important_logger in ["main_runner", "orchestrator", "queue_manager", "worker.ig_v2", "worker.researcher", "instagram_scraper_v2"]:
    logging.getLogger(important_logger).setLevel(logging.INFO)

# Silenciar bibliotecas barulhentas
for noisy_logger in ["httpx", "httpcore", "supabase", "postgrest", "urllib3", "playwright"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger("main_runner")

from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor
from workers.ai.suggestion_consumer import SuggestionConsumer
from workers.orchestrator.orchestrator import SentinelaOrchestrator
from core.autopilot.manager import autopilot
from core.autopilot.cloud_listener import CloudListener, set_current_cycle

# Workers disponíveis (PASA v52.0):
from workers.scrapers.instagram_worker import InstagramWorker
from workers.ai.target_research_worker import TargetResearchWorker


def build_orchestrator() -> SentinelaOrchestrator:
    store = MemoryStore()
    engine = RewardEngine(store)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory=store, fetcher=fetcher)

    orch = SentinelaOrchestrator(engine, advisor)

    # 🚀 ROCKET MODE: Escalonamento de Scrapers
    num_scrapers = int(os.getenv("NUM_SCRAPER_WORKERS", "1"))
    logger.info(f"[main_runner] Configurando {num_scrapers} Scraper Workers...")
    
    for i in range(num_scrapers):
        worker_id = f"ig-v2-{i+1:02d}"
        orch.register(InstagramWorker(
            worker_id=worker_id,
            config={
                "max_posts": int(os.getenv("MAX_POSTS_PER_PROFILE", "3")),
                "max_comments_per_post": int(os.getenv("MAX_COMMENTS_PER_POST", "50")),
                "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
            },
        ))

    # 🧠 AI PROCESSOR: Worker dedicado para classificação PASA
    # Este worker consome o backlog deixado pelos scrapers
    try:
        from workers.processors.ai_processor_worker import AIProcessorWorker
        orch.register(AIProcessorWorker(
            worker_id="ai-processor-01",
            config={}
        ))
        logger.info("[main_runner] AIProcessorWorker registrado com sucesso.")
    except ImportError:
        logger.warning("[main_runner] AIProcessorWorker ainda não disponível. Pulando registro...")

    # Motor de Curadoria e Inteligência de Alvos (v84.9)
    orch.register(TargetResearchWorker(
        worker_id="researcher-01",
        config={
            "headless": True
        }
    ))

    logger.info(f"[main_runner] Workers registrados: {orch.worker_ids}")
    return orch


def setup_signal_handlers(
    orch: SentinelaOrchestrator,
    loop: asyncio.AbstractEventLoop,
) -> None:
    def _shutdown(sig_name: str) -> None:
        logger.info(f"[main_runner] {sig_name} — encerrando...")
        orch.stop_all()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig.name: _shutdown(s))
        except NotImplementedError:
            pass


async def main() -> None:
    logger.info("[main_runner] Sentinela iniciando...")

    orch = build_orchestrator()

    loop = asyncio.get_running_loop()
    setup_signal_handlers(orch, loop)

    # 🤖 ATIVAÇÃO DO AUTOPILOT L3 (PASA v70.0)
    asyncio.create_task(autopilot.pulse())

    # 🛡️ CONTROLE REMOTO E HEARTBEAT (PASA v80.0)
    cloud_listener = CloudListener(source="local")
    asyncio.create_task(cloud_listener.start())
    logger.info("[main_runner] 🛡️ CloudListener ativado (heartbeat + controle remoto).")

    # 💡 LOOP DE FEEDBACK DO AI ADVISOR (PASA v80.0)
    suggestion_consumer = SuggestionConsumer(orchestrator=orch)
    asyncio.create_task(suggestion_consumer.start())
    logger.info("[main_runner] 💡 SuggestionConsumer ativado (aplicação automática de sugestões).")

    if not orch.worker_ids:
        logger.warning(
            "[main_runner] Nenhum worker ativo. "
            "Mantendo processo vivo para evitar restart loop do Watchdog."
        )
        while True:
            await asyncio.sleep(300)

    await orch.run_all()

    logger.info("[main_runner] Encerrado.")


if __name__ == "__main__":
    asyncio.run(main())
# hot-reload trigger: 2026-05-26 v2
