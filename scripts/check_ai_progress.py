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
    print("📊 Verificando progresso do Processamento de IA...")
    try:
        # Contagem de comentários não processados
        res = await asyncio.to_thread(
            db_client.client.table('comentarios')
            .select('id', count='exact')
            .eq('processado_ia', False)
            .execute
        )
        unprocessed = res.count
        
        # Contagem de comentários com erro
        res_error = await asyncio.to_thread(
            db_client.client.table('comentarios')
            .select('id', count='exact')
            .eq('categoria_ia', 'ERRO')
            .execute
        )
        errors = res_error.count

        # Contagem de comentários SUSPEITOS
        res_suspect = await asyncio.to_thread(
            db_client.client.table('comentarios')
            .select('id', count='exact')
            .eq('categoria_ia', 'SUSPEITO')
            .execute
        )
        suspects = res_suspect.count

        print(f"  - Comentários aguardando IA: {unprocessed}")
        print(f"  - Comentários com categoria ERRO: {errors}")
        print(f"  - Comentários categoria SUSPEITO: {suspects}")
        
    except Exception as e:
        print(f"❌ Erro ao consultar progresso: {e}")

if __name__ == "__main__":
    asyncio.run(check())
