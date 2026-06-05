"""
scripts/run_audit_agent.py
Entry point CLI para o Sub-agente de Auditoria Cruzada Anti-Alucinação.

Uso:
    python scripts/run_audit_agent.py                # ciclo único com padrões
    python scripts/run_audit_agent.py --sample-size 20
    python scripts/run_audit_agent.py --cycles 3     # executa N ciclos
    python scripts/run_audit_agent.py --loop         # roda indefinidamente (a cada 6h)
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

# Configuração de encoding segura para o Windows para evitar UnicodeEncodeError
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

# Carrega variáveis de ambiente antes de importar módulos do projeto
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.ai.sa_audita_classificacoes import SaAuditaClassificacoes
from workers.ai.sa_consulta_banco import SaConsultaBanco

# Logging configurado para o sub-agente
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("audit_agent")

DEFAULT_LOOP_INTERVAL_SECONDS = 6 * 3600


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sub-agente de Auditoria Cruzada Anti-Alucinação - Sentinela"
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
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    db_agent = SaConsultaBanco()
    agent = SaAuditaClassificacoes(database_agent=db_agent)

    cycles_executed = 0
    try:
        while True:
            cycles_executed += 1
            logger.info(f"[SaAuditaClassificacoes] Iniciando ciclo #{cycles_executed}")
            
            result = await agent.run_audit(
                sample_size=args.sample_size,
                confidence_threshold=args.confidence,
                drift_alert_threshold=args.drift_threshold
            )

            if result.get("success"):
                logger.info(
                    "Concluido ciclo #%d | auditados=%d | divergencias=%d | drift=%.1f%% | alerta=%s",
                    cycles_executed,
                    result.get("checked", 0),
                    result.get("discrepancies", 0),
                    result.get("drift_rate_pct", 0.0),
                    result.get("drift_alert", False)
                )
            else:
                logger.error(
                    "Erro no ciclo #%d: %s",
                    cycles_executed,
                    result.get("error", "Erro desconhecido")
                )

            if not args.loop and cycles_executed >= args.cycles:
                break

            if args.loop:
                logger.info("Próximo ciclo em %.0fh. Aguardando...", args.interval / 3600)
                await asyncio.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("Interrupção detectada. Encerrando...")
    finally:
        logger.info("SaAuditaClassificacoes encerrado. Total de ciclos: %d.", cycles_executed)


def main() -> None:
    args = parse_args()
    logger.info("SaAuditaClassificacoes iniciando | sample=%d | confidence>=%.0f%% | drift_alerta=%.0f%%",
                args.sample_size, args.confidence * 100, args.drift_threshold)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

