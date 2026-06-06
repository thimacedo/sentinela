import os
import sys
import subprocess
import logging
import time
import psutil # Necessário para inspeção granular

logger = logging.getLogger("core.process_cleaner")

def cleanup_orphans(kill_ollama: bool = False):
    """
    Limpa processos órfãos e duplicados (PASA v88.5).
    """
    current_pid = os.getpid()
    
    # 1. Limpeza de Navegadores (Playwright)
    if os.name == 'nt': # Windows
        try:
            # v50.1: CREATE_NO_WINDOW flag para evitar popups no Windows
            flags = 0x08000000 
            # Mata processos de automação headless
            subprocess.run('wmic process where "CommandLine like \'%--headless%\' and name=\'chrome.exe\'" call terminate', shell=True, capture_output=True, creationflags=flags)
            subprocess.run('wmic process where "CommandLine like \'%--headless%\' and name=\'msedge.exe\'" call terminate', shell=True, capture_output=True, creationflags=flags)
            subprocess.run('wmic process where "ExecutablePath like \'%ms-playwright%\'" call terminate', shell=True, capture_output=True, creationflags=flags)
            subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe", "/T"], capture_output=True, check=False, creationflags=flags)
        except Exception:
            pass
    else: # Linux
        try:
            subprocess.run(["pkill", "-9", "-f", "playwright"], capture_output=True, check=False)
        except Exception:
            pass

    # 2. Limpeza de Processos Python Duplicados (Scripts do Sentinela)
    # Evita que múltiplas instâncias do main_runner ou workers rodem fora do controle do orquestrador
    sentinela_scripts = ["main_runner.py", "watchdog_duplicate_killer.py", "run_doc_fetcher.py"]
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Ignora o processo atual
            if proc.info['pid'] == current_pid:
                continue
                
            cmdline = " ".join(proc.info['cmdline'] or [])
            
            # Limpeza de Ollama (se solicitado ou se houver múltiplos)
            if "ollama" in proc.info['name'].lower() or "ollama" in cmdline.lower():
                if kill_ollama:
                    logger.warning(f"🧹 [Cleaner] Encerrando Ollama (PID {proc.info['pid']})")
                    proc.kill()
            
            # Limpeza de scripts Python do projeto
            if "python" in proc.info['name'].lower():
                if any(script in cmdline for script in sentinela_scripts):
                    # v89.0: Proteção extra para não se auto-encerrar
                    # Verifica se o PID é o atual ou o PAI do atual (para casos de subprocess/watchdog)
                    if proc.info['pid'] == current_pid or proc.info['pid'] == os.getppid():
                        continue
                    
                    logger.warning(f"🧹 [Cleaner] Encerrando script Python órfão: {cmdline} (PID {proc.info['pid']})")
                    proc.kill()
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    logger.info("🧹 [Cleaner] Faxina de processos concluída.")

def ensure_ollama_singleton():
    """
    Garante que exista apenas UMA instância do Ollama rodando.
    Se houver mais de uma, mata todas para que o health_check reinicie apenas uma.
    """
    ollama_procs = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if "ollama" in proc.info['name'].lower():
                ollama_procs.append(proc)
        except: continue
        
    if len(ollama_procs) > 1:
        logger.warning(f"⚠️ Detectadas {len(ollama_procs)} instâncias do Ollama. Resetando para evitar overhead.")
        for p in ollama_procs:
            try: p.kill()
            except: pass
        time.sleep(1)
        return False
    return len(ollama_procs) == 1

if __name__ == "__main__":
    cleanup_orphans()
