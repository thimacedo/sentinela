from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/main_runner.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("main_runner")

from workers.base.memory_store import MemoryStore
from workers.base.reward_engine import RewardEngine
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.ai_advisor import AIAdvisor
from workers.orchestrator.orchestrator import SentinelaOrchestrator

# Workers disponíveis — ativar conforme validação:
# from workers.scrapers.ig_headless import IGHeadlessWorker
# from workers.scrapers.ig_zyte import IGZyteWorker


def build_orchestrator() -> SentinelaOrchestrator:
    store = MemoryStore()
    engine = RewardEngine(store)
    fetcher = DocFetcher()
    advisor = AIAdvisor(memory=store, fetcher=fetcher)

    orch = SentinelaOrchestrator(engine, advisor)

    # Exemplo de ativação segura:
    # zyte_key = os.getenv("ZYTE_API_KEY")
    # if zyte_key:
    #     orch.register(IGZyteWorker(worker_id="ig-zyte-01", config={"api_key": zyte_key}))
    # else:
    #     logger.warning("[main_runner] ZYTE_API_KEY ausente.")

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
