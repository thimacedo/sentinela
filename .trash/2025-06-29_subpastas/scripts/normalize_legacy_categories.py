import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env", override=True)

from core.db import db_client
from core.ai_service import ai_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NormalizeCategories")

async def normalize_batch(limit=50):
    legacy_cats = ['POSITIVO', 'NEGATIVO', 'HATE', 'MILICIA_DIGITAL']
    
    logger.info(f"🔍 Buscando até {limit} comentários com categorias legadas: {legacy_cats}")
    
    try:
        res = await asyncio.to_thread(
            db_client.client.table('comentarios')
            .select('id, texto_bruto, texto_limpo, candidato_id')
            .in_('categoria_ia', legacy_cats)
            .limit(limit)
            .execute
        )
        
        items = res.data or []
        if not items:
            logger.info("✅ Nenhum comentário legado encontrado.")
            return

        logger.info(f"⚙️ Processando {len(items)} comentários...")
        
        for item in items:
            text = item.get('texto_limpo') or item.get('texto_bruto')
            if not text:
                continue
                
            logger.info(f"  - Re-analisando ID {item['id']}...")
            
            # Re-classifica usando a malha de IA (MCA v2.2)
            # PASA v88.2: Usamos o classificador unificado
            result = await ai_service.classify_text(text, item['candidato_id'])
            
            # Atualiza no banco
            await asyncio.to_thread(
                db_client.client.table('comentarios')
                .update({
                    "categoria_ia": result.get("categoria_ia"),
                    "confianca_ia": result.get("confianca_ia", 0.0),
                    "analise_pericial": result.get("analise_pericial"),
                    "processado_ia": True
                })
                .eq("id", item['id'])
                .execute
            )
            
        logger.info(f"✅ Lote de {len(items)} comentários normalizado com sucesso.")

    except Exception as e:
        logger.error(f"❌ Erro na normalização: {e}")

if __name__ == "__main__":
    asyncio.run(normalize_batch(50))
