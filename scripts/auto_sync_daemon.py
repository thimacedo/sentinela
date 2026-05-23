# -*- coding: utf-8 -*-
"""
auto_sync_daemon.py — Daemon que monitora o progresso da reclassificação e
sincroniza com o Supabase quando há novos lotes de registros prontos.
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path

# ── raiz do projeto ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Configurar logging
LOG_FILE = Path(__file__).with_name("auto_sync_daemon.log")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("auto_sync")

PROGRESS_FILE = Path(__file__).parent / "reclassify_csv_progress.json"
STATE_FILE = Path(__file__).parent / "sync_reclassified_state.json"
CSV_INPUT = ROOT / "comentários_neutros.csv"
SYNC_SCRIPT = Path(__file__).parent / "sync_reclassified_to_supabase.py"

def count_total_neutral() -> int:
    """Conta quantos registros precisam ser reclassificados no CSV de entrada."""
    if not CSV_INPUT.exists():
        return 0
    try:
        import csv
        with open(CSV_INPUT, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return sum(1 for r in reader if r.get("texto_bruto", "").strip())
    except Exception as e:
        log.error(f"Erro ao ler CSV de entrada para contagem: {e}")
        return 0

def get_counts() -> tuple[int, int]:
    """Retorna (quantidade_no_progresso, quantidade_sincronizada)."""
    prog_count = 0
    state_count = 0
    
    if PROGRESS_FILE.exists():
        try:
            prog = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            prog_count = len(prog)
        except Exception:
            pass
            
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            state_count = len(state)
        except Exception:
            pass
            
    return prog_count, state_count

def run_sync():
    """Chama o script de sincronização."""
    log.info("Disparando sincronização com o Supabase...")
    try:
        # Roda o script de sincronização e aguarda finalizar
        res = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT)],
            capture_output=True,
            check=True
        )
        log.info("Sincronização concluída com sucesso.")
        stdout_str = res.stdout.decode('utf-8', errors='replace')
        # Loga as últimas linhas do output do script de sincronização
        lines = stdout_str.splitlines()
        for line in lines[-5:]:
            log.info(f"[sync_output] {line}")
    except subprocess.CalledProcessError as e:
        stderr_str = e.stderr.decode('utf-8', errors='replace') if e.stderr else ""
        log.error(f"Erro ao executar script de sincronização: {stderr_str}")
    except Exception as e:
        log.error(f"Erro inesperado no disparo de sincronização: {e}")

def main():
    log.info("=" * 60)
    log.info("Iniciando Daemon de Sincronização Automática...")
    log.info(f"Monitorando progresso local a cada 180 segundos.")
    log.info("=" * 60)
    
    total_neutros = count_total_neutral()
    log.info(f"Total de comentários neutros mapeados no CSV: {total_neutros}")
    
    check_interval = 180  # 3 minutos
    
    while True:
        try:
            prog_count, state_count = get_counts()
            pending_sync = prog_count - state_count
            
            log.info(
                f"Status: Reclassificados localmente: {prog_count}/{total_neutros} | "
                f"Sincronizados no Supabase: {state_count} | "
                f"Pendentes de Sync: {pending_sync}"
            )
            
            # Se acumulou uma quantidade considerável (ex: >= 100) para sync
            if pending_sync >= 100:
                log.info(f"Quantidade considerável acumulada ({pending_sync} registros).")
                run_sync()
            
            # Se a tarefa de reclassificação terminou (todos reclassificados localmente)
            elif prog_count >= total_neutros and total_neutros > 0:
                log.info("A reclassificação local terminou! Executando sincronização final...")
                run_sync()
                log.info("Daemon encerrando atividades. Todos os registros foram reclassificados e sincronizados.")
                break
                
            # Verifica se o processo principal reclassify_csv.py ainda está rodando
            # Se o processo não estiver rodando e houver qualquer registro pendente, sincroniza e encerra.
            # No Windows, procuramos na lista de processos do sistema por "reclassify_csv.py"
            is_main_running = False
            try:
                import psutil
                for proc in psutil.process_iter(['cmdline']):
                    cmd = proc.info.get('cmdline') or []
                    cmd_str = " ".join(cmd)
                    if "reclassify_csv.py" in cmd_str and "auto_sync_daemon" not in cmd_str:
                        is_main_running = True
                        break
            except ImportError:
                # Se psutil não estiver instalado, usamos comando tasklist como fallback alternativo
                try:
                    out = subprocess.check_output("wmic process get CommandLine", shell=True, text=True)
                    if "reclassify_csv.py" in out and "auto_sync_daemon" not in out:
                        is_main_running = True
                except Exception:
                    is_main_running = True # Assume rodando se falhar a detecção
            
            if not is_main_running and pending_sync > 0:
                log.info("O processo principal reclassify_csv.py não está mais rodando.")
                log.info(f"Sincronizando os {pending_sync} registros pendentes restantes...")
                run_sync()
                log.info("Daemon encerrando atividades devido à inatividade do processo principal.")
                break
                
            elif not is_main_running and pending_sync == 0:
                log.info("Processo principal finalizado e sem registros pendentes de sincronização.")
                break

        except Exception as e:
            log.error(f"Erro no loop do daemon: {e}")
            
        time.sleep(check_interval)

if __name__ == "__main__":
    main()
