import os
import sys
import subprocess

# Localiza a raiz do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if __name__ == "__main__":
    # Roda o módulo unificado do watchdog com a flag --background para auto-desacoplar no Windows
    python_exe = sys.executable
    print(f"[Tray-Redirect] Iniciando watchdog unificado na bandeja (modo background)...")
    subprocess.Popen(
        [python_exe, "-m", "watchdog", "--background"],
        cwd=PROJECT_ROOT
    )
    sys.exit(0)
