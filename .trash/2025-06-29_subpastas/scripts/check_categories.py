import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env", override=True)

from core.db import db_client

async def check():
    print("📊 Verificando volumes de Categorias IA...")
    legacy_cats = ['POSITIVO', 'NEGATIVO', 'HATE', 'MILICIA_DIGITAL']
    mca_cats = ['ODIO_IDENTITARIO', 'VIOLENCIA_GENERO', 'AMEACA', 'INSULTO_AD_HOMINEM', 'ATAQUE_INSTITUCIONAL', 'DANO_A_IMAGEM', 'NEUTRO', 'SUSPEITO', 'ERRO']
    
    try:
        print("\n--- Categorias MCA v2.2 (Modernas) ---")
        for cat in mca_cats:
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id', count='exact').eq('categoria_ia', cat).execute
            )
            print(f"  - {cat:<20}: {res.count}")

        print("\n--- Categorias Legadas (A Normalizar) ---")
        for cat in legacy_cats:
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id', count='exact').eq('categoria_ia', cat).execute
            )
            print(f"  - {cat:<20}: {res.count}")

        res_null = await asyncio.to_thread(
            db_client.client.table('comentarios').select('id', count='exact').is_('categoria_ia', 'null').execute
        )
        print(f"\n  - {'NULL (Não Processado)':<20}: {res_null.count}")

    except Exception as e:
        print(f"❌ Erro ao consultar categorias: {e}")

if __name__ == "__main__":
    asyncio.run(check())
