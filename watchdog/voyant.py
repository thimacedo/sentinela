import os
import subprocess
import shutil
import time

def run_voyant_server(project_root):
    try:
        # Tenta usar javaw.exe para evitar console, fallback para java
        java_path = shutil.which("javaw") or shutil.which("java")
        if not java_path:
            print("[WARN] Java não encontrado no PATH. VoyantServer não iniciado.")
            return
        
        jar_path = os.path.join(project_root, "tools", "voyant", "VoyantServer.jar")
        voyant_dir = os.path.dirname(jar_path)
        creationflags = 0x08000000 if os.name == 'nt' else 0
        
        subprocess.Popen(
            [java_path, "-Xmx512m", "-jar", jar_path],
            creationflags=creationflags,
            cwd=voyant_dir
        )
        print("[START] Motor Léxico (VoyantServer) iniciado em modo background no diretório " + voyant_dir)
    except Exception as e_voyant:
        print(f"[WARN] Falha ao iniciar VoyantServer: {e_voyant}")
