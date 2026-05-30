"""
Sentinela Cloud Queue Refresh (v80.1)
Garante a repopulação e integridade da fila de coleta (fila_coleta) do Supabase.
Executado periodicamente via GitHub Actions.
"""
from __future__ import annotations

import os
import sys
import logging

# Força UTF-8 no Windows para evitar UnicodeEncodeError no console local
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass


# --- Auto-Anchoring (PASA v80.1) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cloud_queue_refresh")

def main():
    logger.info("Iniciando verificação e repopulação da fila de coleta da Sentinela...")
    
    try:
        from core.supabase_service import supabase
        from core.queue_manager import QueueManager
        
        manager = QueueManager(supabase)
        
        # Garante pelo menos 50 itens pendentes na fila
        min_pending = 50
        logger.info(f"Executando verificação de população da fila (meta mínima: {min_pending} pendentes)...")
        manager._ensure_queue_populated(min_pending=min_pending)
        
        logger.info("Verificação da fila concluída com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao repopular fila de coleta: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
