"""
scripts/run_dossier_agent.py
Entry point CLI para o Sub-agente de Geração de Dossiês em PDF.

Uso:
    python scripts/run_dossier_agent.py                  # ciclo único
    python scripts/run_dossier_agent.py --loop           # roda em loop a cada 60s
    python scripts/run_dossier_agent.py --interval 120   # intervalo personalizado (segundos)
    python scripts/run_dossier_agent.py --report-dir /caminho/reports
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.processors.dossier_worker import DossierWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dossier_agent")

DEFAULT_INTERVAL = 60  # segundos entre ciclos no modo loop


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sub-agente de Geração de Dossiês — Sentinela PASA v88.0"
    )
    parser.add_argument(
        "--report-dir", type=str, default="reports",
        help="Diretório onde os PDFs serão salvos (padrão: reports/)."
    )
    parser.add_argument(
        "--loop", action="store_true",
        help=f"Executa em loop contínuo (padrão: intervalo de {DEFAULT_INTERVAL}s)."
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL,
        help=f"Intervalo em segundos entre ciclos no modo --loop (padrão: {DEFAULT_INTERVAL}s)."
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    config = {"report_dir": args.report_dir}
    worker = DossierWorker(worker_id="dossier_agent", config=config)
    shutdown_event = asyncio.Event()
    worker.shutdown_event = shutdown_event

    await worker.setup()

    cycles = 0
    try:
        while True:
            result = await worker.run_cycle()
            cycles += 1

            logger.info(
                "📊 Ciclo #%d | pendentes=%d | gerados=%d | falhas=%d | erro=%s",
                result.cycle,
                result.extracted,
                result.inserted,
                result.failed,
                result.error or "nenhum",
            )

            if not args.loop:
                break

            logger.info("😴 Aguardando %ds até próximo ciclo...", args.interval)
            await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("⛔ Interrupção detectada. Encerrando gracefully...")
        shutdown_event.set()
    finally:
        await worker.teardown()
        logger.info("✅ DossierAgent encerrado. Total de ciclos: %d.", cycles)


def main() -> None:
    args = parse_args()
    logger.info("🚀 DossierAgent iniciando | dir=%s | loop=%s", args.report_dir, args.loop)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
