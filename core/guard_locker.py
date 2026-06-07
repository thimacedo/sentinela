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

    def _cleanup_zombies(self):
        """Mata processos python zumbis que ficaram presos (Anti-Shim v90.7)."""
        if os.name != 'nt': return
        try:
            current_pid = os.getpid()
            script_name = f"{self.name}.py" if not self.name.endswith(".py") else self.name
            
            # Busca processos python.exe
            cmd = 'wmic process where "name=\'python.exe\'" get processid,commandline'
            output = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode('utf-8', errors='ignore')
            
            pids_to_kill = []
            for line in output.splitlines():
                if not line.strip():
                    continue
                # Filtra pelo nome do script no commandline e exclui o próprio processo
                if script_name in line:
                    parts = line.strip().split()
                    if parts and parts[-1].isdigit():
                        pid = int(parts[-1])
                        if pid != current_pid:
                            # Verificação extra: loga o cmdline antes de matar para auditoria
                            cmdline_preview = line.strip()[:120]
                            logger.warning(f"🧹 [{self.name}] Zumbi identificado — PID {pid} | cmdline: {cmdline_preview}")
                            pids_to_kill.append(pid)
            
            for pid in pids_to_kill:
                logger.warning(f"🧹 [{self.name}] Faxina de zumbi órfão detectado: PID {pid}")
                self._terminate(pid)
        except Exception as e:
            logger.debug(f"Falha na faxina de zumbis: {e}")

    def acquire(self, kill_existing: bool = True) -> bool:
        """Tenta adquirir o lock de instância única."""
        current_pid = os.getpid()
        
        if kill_existing:
            self._cleanup_zombies()

        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    content = f.read().strip()
                    old_pid = int(content) if content.isdigit() else None
                
                if old_pid == current_pid:
                    return True
                
                if old_pid and self._is_running(old_pid):
                    if kill_existing:
                        logger.warning(f"🚨 [{self.name}] Lock ocupado (PID {old_pid}). Forçando liberação...")
                        self._terminate(old_pid)
                        time.sleep(1.5) # Tempo extra para o SO
                    else:
                        logger.error(f"❌ [{self.name}] Bloqueado: Outra instância ativa (PID {old_pid}).")
                        return False
            except Exception:
                pass 

        try:
            # Garante diretório
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
            with open(self.lock_file, "w") as f:
                f.write(str(current_pid))
            return True
        except Exception as e:
            logger.error(f"❌ [{self.name}] Erro fatal ao gravar lock: {e}")
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
