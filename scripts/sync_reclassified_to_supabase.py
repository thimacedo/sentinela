# -*- coding: utf-8 -*-
"""
sync_reclassified_to_supabase.py — Sincroniza o progresso local de reclassificação com o Supabase remoto.

Lê o progresso em scripts/reclassify_csv_progress.json e atualiza a tabela 'comentarios'
no Supabase remoto para os registros reclassificados que ainda não foram sincronizados.
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# ── raiz do projeto ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Configurar logging
LOG_FILE = Path(__file__).with_name("sync_reclassified.log")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("sync_supabase")

from core.supabase_service import supabase

# Arquivo para registrar o que já foi enviado ao Supabase
SYNC_STATE_FILE = Path(__file__).with_name("sync_reclassified_state.json")
PROGRESS_FILE = Path(__file__).parent / "reclassify_csv_progress.json"

def load_sync_state() -> set:
    if SYNC_STATE_FILE.exists():
        try:
            return set(json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8")))
        except Exception as e:
            log.warning(f"Falha ao ler estado de sincronização: {e}")
    return set()

def save_sync_state(synced_ids: set):
    try:
        SYNC_STATE_FILE.write_text(
            json.dumps(list(synced_ids), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        log.error(f"Erro ao salvar estado de sincronização: {e}")

async def sync_single(comment_id: str, data: dict, semaphore: asyncio.Semaphore) -> bool:
    async with semaphore:
        try:
            update_payload = {
                "categoria_ia": data["categoria_ia"],
                "confianca_ia": data["confianca_ia"],
                "is_hate": data["is_hate"],
                "processado_ia": True
            }
            
            # Executa a atualização no Supabase em uma thread pool se o cliente do Supabase for síncrono
            # O cliente supabase-py padrão é síncrono. Vamos rodar em loop.run_in_executor para não bloquear o loop de eventos.
            loop = asyncio.get_running_loop()
            
            def run_update():
                return supabase.table("comentarios").update(update_payload).eq("id", comment_id).execute()
                
            await loop.run_in_executor(None, run_update)
            return True
        except Exception as e:
            log.error(f"Erro ao atualizar comentário {comment_id} no Supabase: {e}")
            return False

async def main():
    log.info("=" * 60)
    log.info(f"Iniciando sincronização com Supabase | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Progresso: {PROGRESS_FILE}")
    log.info(f"Estado de Sincronização: {SYNC_STATE_FILE}")
    log.info("=" * 60)

    if not PROGRESS_FILE.exists():
        log.error(f"Arquivo de progresso {PROGRESS_FILE} não existe. Nada a sincronizar.")
        return

    try:
        progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"Erro ao carregar arquivo de progresso: {e}")
        return

    synced_ids = load_sync_state()
    log.info(f"Registros já sincronizados anteriormente: {len(synced_ids)}")

    # Filtra o que está no progresso mas ainda não foi sincronizado
    to_sync = {k: v for k, v in progress.items() if k not in synced_ids}
    log.info(f"Registros pendentes para sincronização no Supabase: {len(to_sync)}")

    if not to_sync:
        log.info("Nenhum registro novo para sincronizar.")
        return

    # Limita concorrência para evitar problemas de limite de conexão ou sobrecarga
    semaphore = asyncio.Semaphore(15)
    
    success_count = 0
    errors_count = 0
    
    tasks = []
    for comment_id, data in to_sync.items():
        tasks.append((comment_id, sync_single(comment_id, data, semaphore)))

    log.info(f"Iniciando atualização de {len(tasks)} registros...")
    
    # Processa em lotes de 100 para ir gravando o estado incrementalmente
    chunk_size = 100
    task_items = list(tasks)
    
    for idx in range(0, len(task_items), chunk_size):
        chunk = task_items[idx:idx + chunk_size]
        chunk_ids = [item[0] for item in chunk]
        chunk_tasks = [item[1] for item in chunk]
        
        results = await asyncio.gather(*chunk_tasks)
        
        # Registra sucessos
        for cid, success in zip(chunk_ids, results):
            if success:
                synced_ids.add(cid)
                success_count += 1
            else:
                errors_count += 1
                
        save_sync_state(synced_ids)
        log.info(f"Progresso: {success_count}/{len(to_sync)} sincronizados com sucesso. Erros: {errors_count}")

    log.info("=" * 60)
    log.info(f"SINCRONIZAÇÃO CONCLUÍDA | Sucessos: {success_count} | Erros: {errors_count}")
    log.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
