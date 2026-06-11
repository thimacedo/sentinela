import os
import sys
import subprocess
import time
import socket

# Localiza a raiz do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def is_watchdog_running():
    """Tenta conectar na porta 8009 para ver se o watchdog já está ouvindo."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 8009))
        s.close()
        return True
    except Exception:
        return False

if __name__ == "__main__":
    if is_watchdog_running():
        print("[OK] Watchdog já está em execução.")
        sys.exit(0)

    # v52.8: Força o uso do pythonw.exe BASE do sistema (evita shims de venv/uv que vazam console)
    base_dir = getattr(sys, "base_prefix", sys.prefix)
    pythonw_exe = os.path.join(base_dir, "pythonw.exe")
    
    if not os.path.exists(pythonw_exe):
        # Fallback para o venv se o base não tiver
        pythonw_exe = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "pythonw.exe")
    
    creationflags = 0x08000000 | 0x00000008 | 0x00000200 # CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    
    print(f"[START] Disparando Watchdog Invisible via pythonw base ({pythonw_exe})...")
    
    # Redireciona logs para arquivo
    log_path = os.path.join(PROJECT_ROOT, "runtime_state", "watchdog_bg.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, "a") as log_file:
        # Prepara o ambiente do venv explicitamente para o interpretador base
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = os.path.join(PROJECT_ROOT, ".venv")
        # v52.9: Adiciona site-packages do venv ao PYTHONPATH para o interpretador base achar os pacotes
        site_packages = os.path.join(PROJECT_ROOT, ".venv", "Lib", "site-packages")
        env["PYTHONPATH"] = site_packages + os.pathsep + env.get("PYTHONPATH", "")
        
        subprocess.Popen(
            [pythonw_exe, "-m", "watchdog", "--background", "--detached"],
            cwd=PROJECT_ROOT,
            creationflags=creationflags,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            env=env
        )
    
    # Aguarda confirmação de bind
    time.sleep(2)
    if is_watchdog_running():
        print("[SUCCESS] Watchdog Tray agora é independente. Pode fechar esta janela.")
    else:
        print("[WARN] Watchdog disparado, mas porta 8009 ainda não responde. Verifique watchdog_bg.log.")
    
    sys.exit(0)
