# Cronjob SRE Backup Sync (cj_sre_backup_sync)
# Arquivo: scripts/cj_sre_backup_sync.py

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configura caminhos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

# Logger básico configurado de forma limpa para evitar CP1252 exceptions no Windows console
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sre.backup_sync")

from core.supabase_client import get_supabase_client
from core.local_buffer import LocalBuffer

async def main():
    logger.info("=" * 60)
    logger.info("INICIANDO SINCRONIZAÇÃO DE BACKUP SRE (cj_sre_backup_sync)")
    logger.info("=" * 60)
    
    # Instancia o LocalBuffer
    buffer = LocalBuffer()
    pending_count = buffer.get_count()
    
    if pending_count == 0:
        logger.info("[Sync] Nenhum comentario pendente no buffer local SQLite.")
        logger.info("=" * 60)
        return

    logger.info(f"[Sync] Encontrados {pending_count} comentarios pendentes localmente. Iniciando upload...")
    
    try:
        db = get_supabase_client()
        # Executa a sincronização usando o método nativo do LocalBuffer
        synced = await buffer.sync_with_supabase(db)
        
        remaining = buffer.get_count()
        logger.info(f"✅ [Sync] Sucesso! Sincronizados: {synced} | Restantes no buffer: {remaining}")
        
    except Exception as e:
        logger.error(f"❌ [Sync] Falha na sincronizacao: {e}")
        
    logger.info("=" * 60)
    logger.info("PROCESSO DE SINCRONIZAÇÃO FINALIZADO")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
