"""
PASA v34.1 - Long Course Scraper: Raspagem completa, lenta e humana.
Pausas respiradas de 30s a 90s entre cada perfil para evitar qualquer shadowban.
"""
import time
import random
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.supabase_service import get_supabase_client
from app.workers.instagram_worker import InstagramWorker

def run_long_course():
    db = get_supabase_client()
    worker = InstagramWorker()
    
    print("[LongScrape] Iniciando raspagem de Longo Curso. Sem pressa.")
    
    while True:
        # Busca o próximo alvo pendente (Um por vez para evitar lock)
        pending = db.table('fila_coleta')\
            .select('id, candidato_id')\
            .eq('status', 'PENDENTE')\
            .limit(1)\
            .execute()
            
        if not pending.data:
            print("[LongScrape] Fila esvaziada. Missão completa.")
            break
            
        item = pending.data[0]
        target_id = item['candidato_id']
        item_id = item['id']
        
        print(f"\n[LongScrape] Alvo adquirido: @{target_id}")
        
        try:
            success = worker.run(target=target_id)
            new_status = 'CONCLUIDO' if success else 'FALHA'
            db.table('fila_coleta').update({'status': new_status}).eq('id', item_id).execute()
            print(f"[LongScrape] @{target_id} finalizado: {new_status}")
            
        except Exception as e:
            print(f"[LongScrape] Erro em @{target_id}: {e}")
            db.table('fila_coleta').update({'status': 'FALHA'}).eq('id', item_id).execute()
        
        # A PAUSA RESPIRADA: 30 a 90 segundos aleatórios
        sleep_time = random.uniform(30.0, 90.0)
        print(f"[LongScrape] Descansando {sleep_time:.0f} segundos para mimetizar comportamento humano...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    run_long_course()
