"""
Sentinela Cloud Classify Batch (v80.1)
Executa classificação em lote de comentários pendentes usando o AIService.
"""
import asyncio
import logging
import sys

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cloud_classify_batch")

async def main():
    logger.info("Iniciando processamento em lote da inteligência da Sentinela...")
    
    # Importação tardia do AIService para carregar variáveis após setup do logging
    from core.ai_service import ai_service
    
    # Processa até 100 comentários por execução no workflow do Github Actions
    limit = 100
    try:
        processed_count = await ai_service.run_batch_classification(limit=limit)
        logger.info(f"Ciclo concluído. Total de comentários classificados nesta rodada: {processed_count}")
    except Exception as e:
        logger.error(f"Erro catastrófico no ciclo de classificação: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
