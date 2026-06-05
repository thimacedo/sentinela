import asyncio
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from core.db import db_client

async def check():
    try:
        # Passando a referência do método .execute sem parênteses
        res = await asyncio.to_thread(
            db_client.client.table('comentarios')
            .select('id')
            .eq('categoria_ia', 'SUSPEITO')
            .limit(10)
            .execute
        )
        data = res.data or []
        print(f"SUSPECT_ITEMS_FOUND: {len(data)}")
        
        res_un = await asyncio.to_thread(
            db_client.client.table('comentarios')
            .select('id')
            .eq('processado_ia', False)
            .limit(10)
            .execute
        )
        un_data = res_un.data or []
        print(f"UNPROCESSED_IA_ITEMS: {len(un_data)}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check())
