import os
import subprocess
import httpx
from pathlib import Path

"""Módulo de verificação de saúde para serviços críticos do Sentinela.
Inclui verificações das credenciais do Instagram e garantias de que o
provedor de IA local (Ollama) esteja em execução.
"""

def check_instagram_accounts():
    """Verifica a saúde real das sessões do Instagram no banco (PASA v90.0).
    Retorna o status por conta ou sinaliza 'expired' para alertar o Dashboard.
    Se todas estiverem expiradas, tenta auto-renovação preditiva.
    """
    status = {}
    try:
        import asyncio
        from core.db import db_client
        # Consulta síncrona/async usando o driver
        res = db_client.client.table('worker_sessions').select('username, status').execute()
        sessions = res.data or []
        
        expired_count = 0
        for s in sessions:
            username = s.get('username') or 'Desconhecido'
            s_status = s.get('status', 'expired')
            status[username] = s_status
            if s_status != 'active':
                expired_count += 1
                
        # 🛡️ Gestão Preditiva de Sessões (PASA v90.0)
        # Se 100% das sessões estão expiradas e temos pelo menos 1 registrada, dispara auto-renovação
        if len(sessions) > 0 and expired_count == len(sessions):
            lock_file = Path("runtime_state/session_renewal.lock")
            import time
            
            # Evita disparar scripts simultâneos em menos de 10 minutos
            can_renew = True
            if lock_file.exists():
                mtime = lock_file.stat().st_mtime
                if (time.time() - mtime) < 600:
                    can_renew = False
                    
            if can_renew:
                print("🚨 [HealthCheck] Todas as sessões do Instagram expiraram. Disparando renovação automática em background...")
                lock_file.parent.mkdir(exist_ok=True)
                lock_file.touch()
                
                # Executa o export_playwright_cookies em processo desanexado para não travar o loop
                import subprocess
                import sys
                script_path = str(Path("scripts/export_playwright_cookies.py").absolute())
                is_windows = os.name == 'nt'
                flags = 0x08000000 if is_windows else 0 # CREATE_NO_WINDOW
                subprocess.Popen([sys.executable, script_path, "--force"], creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
    except Exception as e:
        # Fallback genérico para variáveis de ambiente
        accounts = {
            "IG_USER": os.getenv("IG_USER"),
            "IG_USER_1": os.getenv("IG_USER_1"),
        }
        for key, value in accounts.items():
            if value and value.strip():
                status[key] = "OK"
            else:
                status[key] = "MISSING"
                
    return status

def _start_service(name: str, command: list[str]):
    """Inicia um serviço local em background via subprocess.Popen.
    Não verifica se já está rodando; essa responsabilidade cabe ao
    chamador que pode fazer ping ao endpoint de saúde antes.
    """
    try:
        # v50.1: Usando shell=True no Windows para maior resiliência com scripts/batch files
        is_windows = os.name == 'nt'
        creationflags = 0x08000000 if is_windows else 0
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=is_windows, creationflags=creationflags)
        print("[TOOL] Serviço {} iniciado: {}".format(name, ' '.join(command)))
    except Exception as e:
        print(f"[WARN] Falha ao iniciar {name}: {e}")

from urllib.parse import urlparse

def _get_health_url(base_url: str, default_origin: str, path: str) -> str:
    try:
        clean_url = base_url.strip('"\'')
        url_parsed = urlparse(clean_url)
        if url_parsed.scheme and url_parsed.netloc:
            origin = f"{url_parsed.scheme}://{url_parsed.netloc}"
        else:
            origin = default_origin
        return f"{origin}{path}"
    except Exception:
        return f"{default_origin}{path}"

def ensure_ollama_running():
    from core.process_cleaner import ensure_ollama_singleton
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    health_url = _get_health_url(base_url, "http://localhost:11434", "/api/tags")
    
    # 1. Checa se o serviço responde HTTP
    try:
        resp = httpx.get(health_url, timeout=2.0)
        if resp.status_code == 200:
            # 2. Se responde, garante que não há DUPLICATAS no nível do SO
            if ensure_ollama_singleton():
                return True
    except Exception:
        pass
        
    print("[WARN] Ollama não respondendo ou instâncias duplicadas, iniciando serviço...")
    cmd_str = os.getenv("OLLAMA_COMMAND", "ollama serve")
    import shlex
    cmd = shlex.split(cmd_str)
    _start_service("Ollama", cmd)
    return False

def run_startup_health_checks():
    """Executa verificações de saúde na inicialização do Sentinela.
    - Avalia credenciais Instagram.
    - Garante que Ollama esteja operacional.
    """
    print("Executando verificações de saúde na inicialização...")
    ig_status = check_instagram_accounts()
    for acc, st in ig_status.items():
        print(f"[IG] {acc}: {st}")
    ensure_ollama_running()
