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

if __name__ == "__main__":
    os.chdir(WATCHDOG_DIR)
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("[START] Dashboard disponível em: http://localhost:8001")
    print("[SHIELD] SENTINELA DEMOCRÁTICA - WATCHDOG v50.0")
    guard()
