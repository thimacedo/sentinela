import asyncio
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from workers.scrapers.ig_zyte import IGZyteWorker, Target

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("validation_db_ia")

async def validate_persistence_and_ia():
    load_dotenv()
    
    worker = IGZyteWorker("val-db-ia-01", {"max_posts": 1})
    await worker.setup()
    
    target = Target(username="lulaoficial", candidato_id=None, source="db_validation")
    
    # Comentário Mockado para Prova de Persistência Real
    mock_comments = [
        {
            "id_externo": f"val_test_{int(datetime.now().timestamp())}",
            "texto_bruto": "Teste de validação Sentinela v50.1. A democracia é fundamental.",
            "autor_username": "sentinela_validator",
            "data_publicacao": datetime.now(timezone.utc).isoformat(),
            "data_coleta": datetime.now(timezone.utc).isoformat(),
            "post_shortcode": "C_VALIDATION",
            "plataforma": "INSTAGRAM",
            "candidato_id": None,
            "processado_ia": False
        }
    ]
    
    logger.info("📡 TESTE: Persistência Real no Supabase")
    persist = worker.persist_comments(target, mock_comments)
    logger.info(f"Resultado: inserted={persist.inserted} | success={persist.success}")
    
    if persist.inserted_ids:
        logger.info("🧠 TESTE: Classificação IA Real (MCA v2.2)")
        classify = await worker.classify_comments(persist.inserted_ids)
        logger.info(f"Resultado: classified={classify.classified} | success={classify.success}")
        
        # Verificar no Banco
        res = worker.db.table("comentarios").select("*").eq("id", persist.inserted_ids[0]).single().execute()
        if res.data:
            c = res.data
            logger.info(f"✅ EVIDÊNCIA NO SUPABASE: ID={c['id']} | Processado={c['processado_ia']} | Categoria={c['categoria_ia']}")
    
    await worker.teardown()

if __name__ == "__main__":
    asyncio.run(validate_persistence_and_ia())
