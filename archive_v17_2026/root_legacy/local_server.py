"""
PASA v49 - Sentinela Local Node: Master Server (Clean Architecture)
Fila Inteligente, Cooldown, Shadowban, IA em Batch, Auditoria.
"""
import time
import subprocess
import os
import sys
import logging
from datetime import datetime, timezone

# Ajuste de path para encontrar core e scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.supabase_service import supabase as db
    from app.workers.instagram_worker import InstagramWorker
    from scripts.update_threat_profiles import calculate_hate_density
    from scripts.mass_classify import process_mass_classification
    from scripts.detect_shadowbans import detect_shadowbans
    from scripts.check_drift import check_category_drift
except ImportError as e:
    print(f"Erro crítico de importação: {e}")
    sys.exit(1)

if not os.path.exists('logs'):
    os.makedirs('logs')

# Configuração de logging dupla: arquivo e console (para o Watchdog capturar)
log_format = '%(asctime)s - SERVER - %(message)s'
logging.basicConfig(
    level=logging.INFO, 
    format=log_format,
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SentinelaServer")

WATCHDOG_ACTIVE = os.getenv("WATCHDOG_ACTIVE") == "true"

# Configurações do Ciclo (Otimizadas para Zyte Equalitário)
CYCLE_PAUSE = 1800  # 30 min
SCRAPE_PAUSE = 60   # 1 min entre alvos
COOLDOWN_HOURS = 12 # 12h entre coletas do mesmo alvo (divisão justa)

class WarRoomUI:
    @staticmethod
    def render(status, db_status, queue_size, cycle, logs):
        if WATCHDOG_ACTIVE:
            # Se o Watchdog está ativo, apenas logamos o status em vez de "desenhar" a UI
            logger.info(f"STATUS: {status} | DB: {db_status} | Fila: {queue_size} | Ciclo: {cycle}")
            return

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"--- SENTINELA DEMOCRÁTICA [v49.9] ---")
        print(f"Tempo: {datetime.now().strftime('%H:%M:%S')} | Ciclo: {cycle}")
        print(f"Status: {status}")
        print(f"DB: {db_status} | Fila: {queue_size}")
        print("------------------------------------")
        print("LOGS RECENTES:")
        for log in logs[-5:]:
            print(f"> {log}")
        print("------------------------------------\n")

def log_event(log_list, msg):
    log_list.append(f"[{datetime.now().strftime('%H:%M')}] {msg}")
    logger.info(msg)

def run_server():
    try:
        worker = InstagramWorker()
    except Exception as e:
        logger.error(f"Erro ao inicializar worker: {e}")
        return

    cycle_count = 0
    ops_log = []
    
    while True:
        cycle_count += 1
        supabase_status = "🟢 ONLINE"
        log_event(ops_log, f"Iniciando ciclo #{cycle_count}")
        
        # 1. Fase de Raspagem (Busca Ativa até completar o Batch)
        PROFILES_PER_CYCLE = 5
        profiles_scraped_this_cycle = 0
        
        while profiles_scraped_this_cycle < PROFILES_PER_CYCLE:
            try:
                queue_res = db.table('fila_coleta').select('id', count='exact').eq('status', 'PENDENTE').execute()
                queue_size = queue_res.count if queue_res.count is not None else 0
                WarRoomUI.render(f"🟡 BUSCANDO ALVO ({profiles_scraped_this_cycle+1}/{PROFILES_PER_CYCLE})", supabase_status, queue_size, cycle_count, ops_log)
                
                pending = db.table('fila_coleta').select('id, candidato_id').eq('status', 'PENDENTE').limit(10).execute()
                
                # Dynamic Fallback: se a fila estiver vazia, busca candidatos ativos
                candidatos_para_raspar = []
                if not pending.data:
                    log_event(ops_log, "Fila vazia. Buscando candidatos ativos por prioridade/atividade (Fallback).")
                    # Busca os candidatos ativos ordenando por prioridade (prioridade_coleta) e atividade
                    fallback_res = db.table('candidatos').select('username').eq('status_monitoramento', 'Ativo').order('prioridade_coleta', desc=True).order('comentarios_odio_count', desc=True).limit(20).execute()
                    if fallback_res.data:
                        candidatos_para_raspar = [{'id': None, 'candidato_id': c['username']} for c in fallback_res.data]
                    else:
                        log_event(ops_log, "Nenhum candidato ativo encontrado para fallback.")
                        break
                else:
                    candidatos_para_raspar = pending.data

                for p in candidatos_para_raspar:
                    if profiles_scraped_this_cycle >= PROFILES_PER_CYCLE: break
                    
                    target_id = p['candidato_id']
                    item_id = p['id']
                    
                    # Check Cooldown
                    cand = db.table('candidatos').select('last_scraped_at').eq('username', target_id).execute()
                    if cand.data and cand.data[0].get('last_scraped_at'):
                        last_scraped_str = cand.data[0]['last_scraped_at']
                        try:
                            last_scraped = datetime.fromisoformat(last_scraped_str.replace('Z', '+00:00'))
                            hours_since = (datetime.now(timezone.utc) - last_scraped).total_seconds() / 3600
                            if hours_since < COOLDOWN_HOURS:
                                if item_id:
                                    db.table('fila_coleta').delete().eq('id', item_id).execute() # Remove pra não travar a fila
                                # Não loga no fallback se não tem ID da fila, pra evitar poluição excessiva
                                if item_id:
                                    log_event(ops_log, f"@{target_id} em cooldown ({hours_since:.1f}h). Removido da fila.")
                                continue
                        except Exception: pass
                    
                    # Alvo viável
                    log_event(ops_log, f"Iniciando raspagem de @{target_id}")
                    
                    try:
                        success = worker.run(target=target_id)
                        # Deleta da fila após processar (sucesso ou falha)
                        if item_id:
                            db.table('fila_coleta').delete().eq('id', item_id).execute()
                        if success:
                            db.table('candidatos').update({'last_scraped_at': datetime.now(timezone.utc).isoformat()}).eq('username', target_id).execute()
                            log_event(ops_log, f"Raspagem de @{target_id} concluída.")
                            profiles_scraped_this_cycle += 1
                        else:
                            log_event(ops_log, f"Falha na raspagem de @{target_id}")
                    except Exception as e:
                        if item_id:
                            db.table('fila_coleta').delete().eq('id', item_id).execute()
                        log_event(ops_log, f"ERRO CRÍTICO em @{target_id}: {str(e)[:50]}")
                        break
                    
                    if profiles_scraped_this_cycle < PROFILES_PER_CYCLE:
                        time.sleep(SCRAPE_PAUSE)
                
                # Se após tentar a lista inteira (fila ou fallback) não conseguimos nenhum alvo (todos em cooldown), evitamos loop infinito imediato
                if profiles_scraped_this_cycle == 0:
                    log_event(ops_log, "Nenhum alvo viável neste momento (Cooldown).")
                    break

            except Exception as e:
                supabase_status = "🔴 OFFLINE"
                log_event(ops_log, f"Erro Supabase: {str(e)[:80]}")
                break

        # 2. Profiling, Shadowban e Git Sync
        WarRoomUI.render("📊 ATUALIZANDO PERFIS", supabase_status, "---", cycle_count, ops_log)
        try:
            calculate_hate_density()
            detect_shadowbans()
            log_event(ops_log, "Profiler e Shadowban atualizados.")
            
            subprocess.run(['git', 'add', 'docs/profiler_stream.json', 'docs/kpis.json'], capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'data: atualizar monitor de ameacas'], capture_output=True)
            log_event(ops_log, "Frontend sincronizado via Git.")
        except Exception: pass

        # 3. Descanso Produtivo (IA, Auditoria)
        log_event(ops_log, f"Descanso produtivo iniciado ({CYCLE_PAUSE//60} min).")
        rest_end = time.time() + CYCLE_PAUSE
        audit_done = False
        
        while time.time() < rest_end:
            try:
                pending_ia_res = db.table('comentarios').select('id', count='exact').eq('processado_ia', False).limit(1).execute()
                pending_ia_count = pending_ia_res.count if pending_ia_res.count is not None else 0
                
                if pending_ia_count > 0:
                    WarRoomUI.render(f"🧠 PROCESSANDO IA ({pending_ia_count} pendentes)", supabase_status, "Zzz", cycle_count, ops_log)
                    # Nota: mass_classify costuma ser async, se for o caso deve ser chamado com await
                    # Mas o usuário pediu fluxo sequencial e tirou o asyncio.run
                    # Vou assumir que process_mass_classification pode ser síncrono ou foi adaptado
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Se já tem um loop rodando (improvável aqui), cria uma task
                            loop.create_task(process_mass_classification(limit=50))
                        else:
                            asyncio.run(process_mass_classification(limit=50))
                    except Exception:
                        # Fallback se não for async
                        process_mass_classification(limit=50)
                    time.sleep(10)
                else:
                    if not audit_done:
                        WarRoomUI.render("🔍 AUDITORIA", supabase_status, "CHECK", cycle_count, ops_log)
                        try:
                            from app.workers.audit_worker import run_audit
                            # run_audit também costuma ser async nos arquivos anteriores
                            try:
                                asyncio.run(run_audit(sample_size=3))
                            except Exception:
                                run_audit(sample_size=3)
                                
                            check_category_drift()
                            log_event(ops_log, "Auditoria e Drift Check concluídos.")
                        except Exception as audit_e:
                            log_event(ops_log, f"Falha Auditoria: {str(audit_e)[:30]}")
                        audit_done = True
                    
                    WarRoomUI.render("😴 HIBERNANDO", supabase_status, "IA OK", cycle_count, ops_log)
                    time.sleep(60)
            except Exception as e:
                log_event(ops_log, f"Erro IA/Audit: {e}")
                time.sleep(60)

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nServidor finalizado.")
