from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

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
root_logger.setLevel(logging.INFO)
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

# Silenciar bibliotecas barulhentas
for noisy_logger in ["httpx", "httpcore", "supabase", "postgrest", "urllib3"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger("main_runner")

from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor
from workers.orchestrator.orchestrator import SentinelaOrchestrator

# Workers disponíveis — ativar conforme validação:
from workers.scrapers.ig_headless import IGHeadlessWorker
from workers.scrapers.ig_zyte import IGZyteWorker


def build_orchestrator() -> SentinelaOrchestrator:
    store = MemoryStore()
    engine = RewardEngine(store)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory=store, fetcher=fetcher)

    orch = SentinelaOrchestrator(engine, advisor)

    zyte_key = os.getenv("ZYTE_API_KEY")
    enable_zyte = os.getenv("ENABLE_ZYTE", "true").lower() == "true"
    if zyte_key and enable_zyte:
        orch.register(IGZyteWorker(
            worker_id="ig-zyte-01",
            config={"api_key": zyte_key},
        ))
    else:
        logger.warning("[main_runner] IGZyteWorker desativado ou ZYTE_API_KEY ausente.")

    session_id = os.getenv("INSTAGRAM_SESSIONID")
    if session_id:
        orch.register(IGHeadlessWorker(
            worker_id="ig-headless-01",
            config={"session_id": session_id},
        ))
    else:
        logger.warning("[main_runner] INSTAGRAM_SESSIONID ausente; IGHeadlessWorker não registrado.")

    logger.info(f"[main_runner] Workers: {orch.worker_ids or ['(nenhum)']}")
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
