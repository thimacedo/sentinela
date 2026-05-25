import os
import subprocess
import logging
import time

logger = logging.getLogger("core.process_cleaner")

def cleanup_orphans():
    """
    Limpa processos órfãos de navegadores e drivers para evitar vazamento de memória (PASA v65.0).
    """
    if os.name == 'nt': # Windows
        targets = ["chromium.exe", "chrome.exe", "msedge.exe", "chromedriver.exe"]
        for target in targets:
            try:
                # /T mata a árvore de processos, /F força
                subprocess.run(["taskkill", "/F", "/IM", target, "/T"], capture_output=True, check=False)
            except Exception:
                pass
    else: # Linux
        targets = ["chromium", "chrome", "playwright"]
        for target in targets:
            try:
                subprocess.run(["pkill", "-9", "-f", target], capture_output=True, check=False)
            except Exception:
                pass
    logger.info("🧹 [Cleaner] Processos órfãos removidos com sucesso.")

if __name__ == "__main__":
    cleanup_orphans()
