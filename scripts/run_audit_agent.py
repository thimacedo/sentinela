"""
scripts/run_audit_agent.py
Entry point CLI para o Sub-agente de Auditoria Cruzada Anti-Alucinação.

Uso:
    python scripts/run_audit_agent.py                # ciclo único com padrões
    python scripts/run_audit_agent.py --sample-size 20
    python scripts/run_audit_agent.py --cycles 3     # executa N ciclos
    python scripts/run_audit_agent.py --loop         # roda indefinidamente (a cada 6h)
    python scripts/run_audit_agent.py --dry-run      # só testa conexões, não auditoria
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Garante que o root do projeto está no PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Carrega variáveis de ambiente antes de importar módulos do projeto
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.audit_worker import AuditWorker
from workers.base.reward_engine import RewardEngine
from workers.base.memory_store import MemoryStore
from workers.ai.ai_advisor import AIAdvisor
from workers.ai.doc_fetcher import DocFetcher

# Logging configurado para o sub-agente
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("audit_agent")

# Intervalo padrão do loop contínuo: 6 horas
DEFAULT_LOOP_INTERVAL_SECONDS = 6 * 3600


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sub-agente de Auditoria Cruzada Anti-Alucinação — Sentinela PASA v88.0"
    )
    parser.add_argument(
        "--sample-size", type=int, default=10,
        help="Quantidade de comentários a auditar por ciclo (padrão: 10)."
    )
    parser.add_argument(
        "--confidence", type=float, default=0.85,
        help="Limiar mínimo de confiança para selecionar comentários (padrão: 0.85)."
    )
    parser.add_argument(
        "--drift-threshold", type=float, default=20.0,
        help="Percentual de drift que dispara alerta (padrão: 20%%)."
    )
    parser.add_argument(
        "--cycles", type=int, default=1,
        help="Número de ciclos a executar antes de encerrar (padrão: 1). Ignorado com --loop."
    )
    parser.add_argument(
        "--loop", action="store_true",
        help=f"Executa em loop contínuo a cada {DEFAULT_LOOP_INTERVAL_SECONDS // 3600}h."
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_LOOP_INTERVAL_SECONDS,
        help="Intervalo em segundos entre ciclos no modo --loop."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Executa apenas setup() e teardown() sem rodar ciclos reais."
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    config = {
        "sample_size": args.sample_size,
        "confidence_threshold": args.confidence,
        "drift_alert_threshold": args.drift_threshold,
    }

    worker = AuditWorker(worker_id="audit_agent", config=config)
    shutdown_event = asyncio.Event()

    # Injeta evento de shutdown (compatível com orquestrador)
    worker.shutdown_event = shutdown_event

    await worker.setup()

    if args.dry_run:
        logger.info("🔍 [dry-run] Setup concluído. Encerrando sem executar ciclos.")
        await worker.teardown()
        return

    # Instancia os helpers necessários pelo BaseWorker (não usados diretamente aqui)
    try:
        memory  = MemoryStore()
        fetcher = DocFetcher()
        advisor = AIAdvisor(memory=memory, fetcher=fetcher)
        reward_engine = RewardEngine(memory=memory)
    except Exception as e:
        logger.warning("⚠️ RewardEngine/AIAdvisor não disponíveis: %s. Continuando sem telemetria.", e)
        reward_engine = None
        advisor = None

    cycles_executed = 0
    try:
        while True:
            result = await worker.run_cycle()

            logger.info(
                "📊 Ciclo #%d concluído | auditados=%d | divergências=%d | drift=%.1f%% | erro=%s",
                result.cycle,
                result.audit_checked,
                result.metadata.get("discrepancies", 0),
                result.metadata.get("drift_rate_pct", 0.0),
                result.error or "nenhum",
            )

            # Persiste métricas se RewardEngine disponível
            if reward_engine:
                try:
                    await reward_engine.process_result(result)
                except Exception as e:
                    logger.debug("RewardEngine indisponível: %s", e)

            cycles_executed += 1

            if not args.loop and cycles_executed >= args.cycles:
                break

            if args.loop:
                logger.info("😴 Próximo ciclo em %.0fh. Aguardando...", args.interval / 3600)
                await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("⛔ Interrupção detectada. Encerrando gracefully...")
        shutdown_event.set()
    finally:
        await worker.teardown()
        logger.info("✅ AuditAgent encerrado. Total de ciclos: %d.", cycles_executed)


def main() -> None:
    args = parse_args()
    logger.info("🚀 AuditAgent iniciando | sample=%d | confidence≥%.0f%% | drift_alerta=%.0f%%",
                args.sample_size, args.confidence * 100, args.drift_threshold)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
