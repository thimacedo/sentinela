from __future__ import annotations
import asyncio
import logging
import os
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

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

# Workers disponíveis — descomente conforme validação:
# from workers.scrapers.ig_headless import IGHeadlessWorker
# from workers.scrapers.ig_zyte import IGZyteWorker


def build_orchestrator() -> SentinelaOrchestrator:
    store   = MemoryStore()
    engine  = RewardEngine(store)
    fetcher = DocFetcher()
    advisor = AIAdvisor(
        groq_api_key=os.environ["GROQ_API_KEY"],
        doc_fetcher=fetcher,
    )
    orch = SentinelaOrchestrator(engine, advisor)

    # orch.register(IGHeadlessWorker(
    #     worker_id="ig-headless-01",
    #     config={"session_id": os.environ["INSTAGRAM_SESSIONID"]},
    # ))
    # orch.register(IGZyteWorker(
    #     worker_id="ig-zyte-01",
    #     config={"api_key": os.environ["ZYTE_API_KEY"]},
    # ))

    logger.info(f"[main_runner] Workers: {orch.worker_ids or ['(nenhum)']}")
    return orch


def setup_signal_handlers(orch: SentinelaOrchestrator, loop: asyncio.AbstractEventLoop):
    def _shutdown(sig_name: str):
        logger.info(f"[main_runner] {sig_name} — encerrando...")
        orch.stop_all()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig.name: _shutdown(s))
        except NotImplementedError:
            pass


async def main():
    logger.info("[main_runner] Sentinela iniciando...")
    orch = build_orchestrator()
    loop = asyncio.get_running_loop()
    setup_signal_handlers(orch, loop)
    if not orch.worker_ids:
        logger.warning("[main_runner] Nenhum worker ativo.")
        return
    await orch.run_all()
    logger.info("[main_runner] Encerrado.")


if __name__ == "__main__":
    asyncio.run(main())
