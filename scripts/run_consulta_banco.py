# scripts/run_consulta_banco.py
import asyncio
import logging
import os
import sys
from pathlib import Path

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.ai.sa_consulta_banco import SaConsultaBanco

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_consulta_banco")

async def main():
    logger.info("Disparando Subagente de Dados (SaConsultaBanco) para consolidar status...")
    db_agent = SaConsultaBanco()
    try:
        logger.info("Consultando estatísticas de hostilidade/ódio por candidato...")
        stats = await db_agent.get_hate_stats()
        print("\n--- Estatísticas de Ódio por Candidato ---")
        for row in stats:
            print(f"Candidato: {row.get('candidato_id')} | Total Comentários: {row.get('total_comentarios')} | Total Ódio: {row.get('total_odio')} | Taxa: {row.get('taxa_odio_percent')}%")
        
        logger.info("Consultando os maiores atacantes do sistema...")
        attackers = await db_agent.get_top_attackers(limit=5)
        print("\n--- Top 5 Atacantes ---")
        for row in attackers:
            print(f"Autor: @{row.get('autor_username')} | Total Ataques (Ódio): {row.get('total_ataques')} | Alvos: {row.get('alvos_atacados')}")
        
        logger.info("Consultando performance da Inteligência Artificial...")
        ia_perf = await db_agent.get_ia_performance()
        print("\n--- Performance de Classificação IA ---")
        for cat, data in ia_perf.items():
            print(f"Categoria: {cat} | Total: {data.get('total')} | Confiança Média: {data.get('confianca_media') or 0.0:.2f}")
        print("------------------------------------------\n")
    except Exception as e:
        logger.error(f"Erro ao consultar banco de dados: {e}")
    finally:
        await db_agent.close()

if __name__ == "__main__":
    asyncio.run(main())
