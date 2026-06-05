"""
scripts/run_scanner_agent.py
Entry point CLI para o Sub-agente CandidateScanner.

Uso:
    python scripts/run_scanner_agent.py                         # ciclo único (padrão)
    python scripts/run_scanner_agent.py --once                  # alias para ciclo único
    python scripts/run_scanner_agent.py --watch                 # monitora pasta continuamente
    python scripts/run_scanner_agent.py --watch --interval 120  # loop a cada 120s
    python scripts/run_scanner_agent.py --base-path /custom     # pasta de PDFs customizada
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# ── Garante que o project root está no PYTHONPATH ──────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Carrega variáveis de ambiente ANTES de importar módulos do projeto ─────
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.processors.wk_escaneia_candidatos import WkEscaneiaCandidatos

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scanner_agent")

DEFAULT_INTERVAL = 60  # segundos entre ciclos no modo --watch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sub-agente CandidateScanner — Sentinela PASA v88.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help=f"Monitora a pasta continuamente (intervalo padrão: {DEFAULT_INTERVAL}s).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executa apenas um ciclo e encerra (comportamento padrão).",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Caminho da pasta de PDFs de pesquisa (padrão: .\\bases_pesquisas).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Intervalo em segundos entre ciclos no modo --watch (padrão: {DEFAULT_INTERVAL}s).",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    """Orquestra a execução do WkEscaneiaCandidatos."""
    config: dict = {}
    if args.base_path:
        config["base_path"] = args.base_path

    worker = WkEscaneiaCandidatos(worker_id="scanner_agent", config=config)
    shutdown_event = asyncio.Event()
    worker.shutdown_event = shutdown_event

    logger.info("🚀 ScannerAgent iniciando | %s", worker.describe())
    await worker.setup()

    cycles = 0
    watch_mode = args.watch and not args.once

    try:
        while True:
            result = await worker.run_cycle()
            cycles += 1

            logger.info(
                "📊 Ciclo #%d | detectados=%d | enfileirados=%d | falhas=%d | erro=%s",
                result.cycle,
                result.extracted,
                result.inserted,
                result.failed,
                result.error or "nenhum",
            )

            # Encerra após o primeiro ciclo se não estiver em modo --watch
            if not watch_mode:
                break

            # Parada graceful se shutdown foi sinalizado
            if shutdown_event.is_set():
                logger.info("⛔ Shutdown sinalizado. Encerrando após ciclo atual.")
                break

            logger.info("😴 Aguardando %ds até próximo ciclo...", args.interval)
            try:
                await asyncio.wait_for(
                    asyncio.shield(asyncio.ensure_future(shutdown_event.wait())),
                    timeout=args.interval,
                )
                # shutdown_event foi setado durante a espera
                logger.info("⛔ Shutdown sinalizado durante espera. Encerrando.")
                break
            except asyncio.TimeoutError:
                # Timeout esperado: próximo ciclo
                pass

    except KeyboardInterrupt:
        logger.info("⛔ Interrupção pelo usuário (Ctrl+C). Encerrando gracefully...")
        shutdown_event.set()
    finally:
        await worker.teardown()
        logger.info(
            "✅ ScannerAgent encerrado. Total de ciclos executados: %d.", cycles
        )


def main() -> None:
    args = parse_args()

    mode = "watch (loop contínuo)" if args.watch and not args.once else "once (ciclo único)"
    logger.info(
        "🔍 ScannerAgent | modo=%s | interval=%ds | base_path=%s",
        mode,
        args.interval,
        args.base_path or ".\\bases_pesquisas",
    )

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
