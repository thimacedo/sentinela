# watchdog/__main__.py
import os
import sys
from threading import Thread

# Garante que o diretório do watchdog e a raiz do projeto estejam no PYTHONPATH
WATCHDOG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(WATCHDOG_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if WATCHDOG_DIR not in sys.path:
    sys.path.insert(0, WATCHDOG_DIR)

from watchdog import guard, run_web_server
import subprocess
import signal
import time

def kill_process_on_port(port: int):
    try:
        creationflags = 0x08000000  # CREATE_NO_WINDOW
        output = subprocess.check_output("netstat -ano", shell=True, creationflags=creationflags).decode('utf-8', errors='ignore')
        for line in output.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = int(parts[-1])
                if pid != os.getpid():
                    print(f"[SHIELD] Detectada instância antiga do Watchdog (PID {pid}) na porta {port}. Encerrando...")
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(2)  # Aguarda liberação do socket
                    except Exception as ex:
                        print(f"[SHIELD] Falha ao encerrar PID {pid}: {ex}")
    except Exception as e:
        print(f"[SHIELD] Falha ao checar conexões da porta {port}: {e}")

if __name__ == "__main__":
    os.chdir(WATCHDOG_DIR)
    kill_process_on_port(8001)
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("[START] Dashboard disponível em: http://localhost:8001")
    print("[SHIELD] SENTINELA DEMOCRÁTICA - WATCHDOG v50.0")
    guard()
