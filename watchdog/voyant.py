import os
import subprocess
import shutil
import time

def run_voyant_server(project_root):
    try:
        # v52.5: Verificação de duplicidade por porta e processo
        creationflags = 0x08000000 if os.name == 'nt' else 0
        
        # Tenta detectar se já existe um Voyant rodando (porta padrão 8888 ou processo jar)
        if os.name == 'nt':
            check_cmd = 'wmic process where "commandline like \'%VoyantServer.jar%\'" get processid'
            existing = subprocess.check_output(check_cmd, shell=True).decode()
            pids = [p.strip() for p in existing.split('\n') if p.strip() and p.strip().isdigit()]
            if pids:
                print(f"[OK] VoyantServer já está ativo (PIDs: {', '.join(pids)}). Ignorando inicialização.")
                return

        # Tenta usar javaw.exe para evitar console, fallback para java
        java_path = shutil.which("javaw") or shutil.which("java")
        if not java_path:
            print("[WARN] Java não encontrado no PATH. VoyantServer não iniciado.")
            return
        
        jar_path = os.path.join(project_root, "tools", "voyant", "VoyantServer.jar")
        voyant_dir = os.path.dirname(jar_path)
        
        subprocess.Popen(
            [java_path, "-Xmx1024m", "-jar", jar_path],
            creationflags=creationflags,
            cwd=voyant_dir  # Isso garante que ele rode dentro de tools/voyant/
        )
        print("[START] Motor Léxico (VoyantServer) iniciado em modo background no diretório " + voyant_dir)
    except Exception as e_voyant:
        print(f"[WARN] Falha ao iniciar VoyantServer: {e_voyant}")
