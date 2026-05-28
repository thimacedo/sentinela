import os
import subprocess
import logging
import time

logger = logging.getLogger("core.process_cleaner")

def cleanup_orphans():
    """
    Limpa processos órfãos de navegadores e drivers de forma SEGURA,
    garantindo que não afete os navegadores de uso pessoal do usuário (PASA v65.1).
    """
    if os.name == 'nt': # Windows
        try:
            # Mata apenas processos de automação que contêm '--headless' ou vêm do diretório 'ms-playwright'
            subprocess.run('wmic process where "CommandLine like \'%--headless%\' and name=\'chrome.exe\'" call terminate', shell=True, capture_output=True)
            subprocess.run('wmic process where "CommandLine like \'%--headless%\' and name=\'msedge.exe\'" call terminate', shell=True, capture_output=True)
            subprocess.run('wmic process where "ExecutablePath like \'%ms-playwright%\'" call terminate', shell=True, capture_output=True)
            
            # Chromedriver é seguro matar, pois é só de automação
            subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe", "/T"], capture_output=True, check=False)
        except Exception:
            pass
    else: # Linux
        try:
            subprocess.run(["pkill", "-9", "-f", "playwright"], capture_output=True, check=False)
        except Exception:
            pass
    logger.info("🧹 [Cleaner] Processos órfãos de automação removidos com segurança.")

if __name__ == "__main__":
    cleanup_orphans()
