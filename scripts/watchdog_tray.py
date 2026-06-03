import os
import sys
# Ensure the project root (one level up) is in PYTHONPATH so that 'watchdog' package can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from watchdog import state

from watchdog_duplicate_killer import main as kill_duplicate_main
import subprocess
import threading
import time
from pathlib import Path

# pystray and Pillow for tray icon
from PIL import Image
import pystray
from pystray import MenuItem as item

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # C:\\Projetos\\sentinela
WATCHDOG_SCRIPT = PROJECT_ROOT / "watchdog" / "__init__.py"
ICON_PATH = PROJECT_ROOT / "logo_branco.png"
DASHBOARD_URL = "http://localhost:8001"  # FastAPI dashboard

# Global reference to the watchdog subprocess
watchdog_process = None

def start_watchdog_hidden():
    """Start the watchdog in a hidden console window (Windows only)."""
    global watchdog_process
    # Primeiro, eliminar processos duplicados de main_runner
    try:
        kill_duplicate_main()
    except Exception as e:
        print(f"[Tray] Erro ao limpar processos duplicados: {e}")
    # Duplicated block removed
    # CREATE_NO_WINDOW hides console; DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP keep watchdog alive after parent exit
    # 0x08000000 = CREATE_NO_WINDOW, 0x00000008 = DETACHED_PROCESS, 0x00000200 = CREATE_NEW_PROCESS_GROUP
    creationflags = 0x08000000 | 0x00000008 | 0x00000200
    watchdog_process = subprocess.Popen(
        [sys.executable, str(WATCHDOG_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        creationflags=creationflags,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Forward stdout / stderr to avoid pipe deadlock
    threading.Thread(target=_pipe_forward, args=(watchdog_process.stdout, "STDOUT"), daemon=True).start()
    threading.Thread(target=_pipe_forward, args=(watchdog_process.stderr, "STDERR"), daemon=True).start()
    print("[Tray] Watchdog started (hidden)")

def _pipe_forward(pipe, label):
    for line in iter(pipe.readline, b""):
        if line:
            print(f"[{label}] {line.decode(errors='replace').rstrip()}")
    pipe.close()

def stop_watchdog():
    global watchdog_process
    if watchdog_process and watchdog_process.poll() is None:
        watchdog_process.terminate()
        watchdog_process.wait(timeout=10)
        print("[Tray] Watchdog stopped")
    else:
        print("[Tray] No active watchdog process")
    watchdog_process = None
    
    # Garante que ao parar o watchdog, a gente mata também o main_runner.py que ficou orfão
    try:
        kill_duplicate_main()
        print("[Tray] Processos orfãos de main_runner.py terminados.")
    except Exception as e:
        print(f"[Tray] Erro ao limpar orfãos de main_runner: {e}")

def start_watchdog_menu():
    """Inicia o watchdog se ainda não estiver rodando (usado a partir do tray)."""
    if watchdog_process is None or watchdog_process.poll() is not None:
        start_watchdog_hidden()
        print("[Tray] Watchdog iniciado via menu")
    else:
        print("[Tray] Watchdog já está em execução")

def restart_watchdog():
    """Reinicia o watchdog, encerrando o processo atual (se houver) e iniciando um novo."""
    stop_watchdog()
    start_watchdog_hidden()
    print("[Tray] Watchdog reiniciado")

AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "run_audit_agent.py"
DOSSIER_SCRIPT = PROJECT_ROOT / "scripts" / "run_dossier_agent.py"
SCANNER_SCRIPT = PROJECT_ROOT / "scripts" / "run_scanner_agent.py"

def open_dashboard():
    try:
        subprocess.Popen(["cmd", "/c", "start", "", DASHBOARD_URL], shell=True)
        print("[Tray] Dashboard opened")
    except Exception as e:
        print(f"[Tray] Failed to open dashboard: {e}")

def run_audit_agent():
    """Dispara o sub-agente de auditoria cruzada em uma janela de console visível."""
    try:
        subprocess.Popen(
            [sys.executable, str(AUDIT_SCRIPT), "--sample-size", "15"],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        print("[Tray] AuditAgent disparado (sample=15)")
    except Exception as e:
        print(f"[Tray] Erro ao disparar AuditAgent: {e}")

def run_dossier_agent():
    """Dispara o sub-agente de geração de dossiês em uma janela de console visível."""
    if not DOSSIER_SCRIPT.exists():
        print("[Tray] DossierAgent ainda não implementado.")
        return
    try:
        subprocess.Popen(
            [sys.executable, str(DOSSIER_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        print("[Tray] DossierAgent disparado")
    except Exception as e:
        print(f"[Tray] Erro ao disparar DossierAgent: {e}")

def run_scanner_agent():
    """Dispara o sub-agente de escaneamento de candidatos em console visível."""
    try:
        subprocess.Popen(
            [sys.executable, str(SCANNER_SCRIPT), '--once'],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        print('[Tray] ScannerAgent disparado')
    except Exception as e:
        print(f'[Tray] Erro ao disparar ScannerAgent: {e}')

def quit_tray(icon, item):
    stop_watchdog()
    icon.stop()

def show_current_task(icon, item):
    """Exibe um resumo da tarefa/estado atual do watchdog na notificação da bandeja."""
    with state.lock:
        status = state.status
        restarts = state.restarts
        code_err = state.code_errors
        alerts = state.alerts
        fast = state.fast_crashes
    msg = (
        f"Status: {status}\n"
        f"Restarts: {restarts}\n"
        f"Erros de código: {code_err}\n"
        f"Alertas enviados: {alerts}\n"
        f"Falhas rápidas: {fast}"
    )
    # Usa notificação da bandeja (pystray) se suportado
    try:
        icon.notify(msg, "Tarefa Atual do Watchdog")
    except Exception:
        print(msg)

def setup_tray():
    # Load icon image; fallback to a simple white square if missing
    if ICON_PATH.exists():
        image = Image.open(ICON_PATH)
    else:
        image = Image.new('RGB', (64, 64), color='white')
    menu = (
        item('Abrir Dashboard', lambda i: open_dashboard()),
        item('Iniciar Watchdog', lambda i: start_watchdog_menu()),
        item('Parar Watchdog', lambda i: stop_watchdog()),
        item('Reiniciar Watchdog', lambda i: restart_watchdog()),
        pystray.Menu.SEPARATOR,
        item('▶ Rodar Auditoria IA', lambda i: run_audit_agent()),
        item('▶ Rodar DossierAgent', lambda i: run_dossier_agent()),
        item('▶ Rodar ScannerAgent', lambda i: run_scanner_agent()),
        pystray.Menu.SEPARATOR,
        item('Sair', quit_tray),
    )
    icon = pystray.Icon("sentinela_watchdog", image, "Sentinela Watchdog", menu)
    # Start watchdog before showing the tray icon
    start_watchdog_hidden()
    icon.run()

if __name__ == "__main__":
    # If not already detached, relaunch this script with DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP
    if "--detached" not in sys.argv:
        # Relaunch self as detached process (no console window)
        det_flags = 0x08000000 | 0x00000008 | 0x00000200  # CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([sys.executable, __file__, "--detached"],
                         creationflags=det_flags,
                         cwd=str(PROJECT_ROOT),
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL,
                         close_fds=True)
        sys.exit(0)
    else:
        setup_tray()

