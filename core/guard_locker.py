import os
import sys
import signal
import time
import logging
import subprocess

logger = logging.getLogger("core.guard_locker")

class GuardLocker:
    """
    Garante instância única de processos críticos e gerencia arquivos .lock (PASA v88.5).
    """
    def __init__(self, name: str, project_root: str):
        self.name = name
        # Força caminho absoluto para evitar desvio de diretório entre interpretadores (uv vs venv)
        self.project_root = "C:\\Projetos\\sentinela"
        self.lock_dir = os.path.join(self.project_root, "runtime_state")
        self.lock_file = os.path.join(self.lock_dir, f"{name}.lock")
        os.makedirs(self.lock_dir, exist_ok=True)

    def acquire(self, kill_existing: bool = True) -> bool:
        """
        Tenta adquirir o lock. Se kill_existing for True, mata o processo antigo.
        """
        current_pid = os.getpid()
        
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    old_pid = int(f.read().strip())
                
                if old_pid == current_pid:
                    return True # Já é o dono
                
                if self._is_running(old_pid):
                    if kill_existing:
                        logger.warning(f"🚨 [{self.name}] Instância duplicada detectada (PID {old_pid}). Encerrando...")
                        self._terminate(old_pid)
                        # Dá um tempo para o SO liberar recursos
                        time.sleep(1.0)
                    else:
                        logger.error(f"❌ [{self.name}] Outra instância já está rodando (PID {old_pid}). Abortando.")
                        return False
            except (ValueError, OSError, Exception):
                pass # Arquivo corrompido ou PID inválido, prossegue

        try:
            with open(self.lock_file, "w") as f:
                f.write(str(current_pid))
            return True
        except Exception as e:
            logger.error(f"❌ [{self.name}] Falha ao gravar arquivo de lock: {e}")
            return False

    def release(self):
        """Libera o lock deletando o arquivo."""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception:
            pass

    def _is_running(self, pid: int) -> bool:
        """Verifica se um PID está ativo no sistema."""
        if os.name == 'nt':
            try:
                creationflags = 0x08000000 # CREATE_NO_WINDOW
                output = subprocess.check_output(
                    f'tasklist /FI "PID eq {pid}" /NH', 
                    shell=True, 
                    creationflags=creationflags
                ).decode('utf-8', errors='ignore')
                return str(pid) in output
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def _terminate(self, pid: int):
        """Encerra um processo de forma agressiva."""
        try:
            if os.name == 'nt':
                # v50.1: CREATE_NO_WINDOW para evitar popups no Windows
                flags = 0x08000000
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True, shell=True, creationflags=flags)
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

def ensure_unique_instance(name: str, project_root: str):
    """Atalho para uso rápido em scripts."""
    locker = GuardLocker(name, project_root)
    if not locker.acquire(kill_existing=True):
        sys.exit(1)
    return locker
