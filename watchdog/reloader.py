import time
import os
import sys
import subprocess
import logging
from threading import Thread

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="[HOT-RELOAD] %(asctime)s - %(message)s")
logger = logging.getLogger("reloader")

class HotReloader:
    """
    Monitora mudanças nos arquivos fonte e reinicia o processo filho.
    Específico para desenvolvimento paralelo (PASA v65.0).
    """
    def __init__(self, script_to_watch: str, watch_dir: str = "."):
        self.script = script_to_watch
        self.watch_dir = watch_dir
        self.process = None
        self.last_mtime = self._get_max_mtime()

    def _get_max_mtime(self):
        max_mtime = 0
        for root, dirs, files in os.walk(self.watch_dir):
            if any(x in root for x in [".git", "__pycache__", ".venv", "logs", "runtime_state"]):
                continue
            for f in files:
                if f.endswith(".py"):
                    mtime = os.path.getmtime(os.path.join(root, f))
                    if mtime > max_mtime:
                        max_mtime = mtime
        return max_mtime

    def start_process(self):
        if self.process:
            logger.info(f"🔄 Mudança detectada. Reiniciando {self.script}...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        logger.info(f"🚀 Iniciando {self.script}...")
        self.process = subprocess.Popen([sys.executable, self.script], env=os.environ)

    def run(self):
        self.start_process()
        try:
            while True:
                time.sleep(2)
                current_mtime = self._get_max_mtime()
                if current_mtime > self.last_mtime:
                    self.last_mtime = current_mtime
                    self.start_process()
        except KeyboardInterrupt:
            if self.process:
                self.process.terminate()

if __name__ == "__main__":
    # Exemplo de uso: python watchdog/reloader.py main_runner.py
    target = sys.argv[1] if len(sys.argv) > 1 else "main_runner.py"
    reloader = HotReloader(target)
    reloader.run()
