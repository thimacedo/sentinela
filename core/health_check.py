import os
import subprocess
import httpx
from pathlib import Path

"""Módulo de verificação de saúde para serviços críticos do Sentinela.
Inclui verificações das credenciais do Instagram e garantias de que os
provedores de IA locais (Ollama e LiteRT) estejam em execução.
"""

def check_instagram_accounts():
    """Verifica se as variáveis de ambiente de contas Instagram estão definidas.
    Retorna um dicionário com status para cada credencial.
    """
    accounts = {
        "IG_USER": os.getenv("IG_USER"),
        "IG_PASS": os.getenv("IG_PASS"),
        "IG_USER_1": os.getenv("IG_USER_1"),
        "IG_PASS_1": os.getenv("IG_PASS_1"),
    }
    status = {}
    for key, value in accounts.items():
        if value and value.strip():
            status[key] = "OK"
        else:
            status[key] = "MISSING (ação manual requerida)"
    return status

def _start_service(name: str, command: list[str]):
    """Inicia um serviço local em background via subprocess.Popen.
    Não verifica se já está rodando; essa responsabilidade cabe ao
    chamador que pode fazer ping ao endpoint de saúde antes.
    """
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    health_url = _get_health_url(base_url, "http://localhost:11434", "/api/tags")
    try:
        resp = httpx.get(health_url, timeout=2.0)
        if resp.status_code == 200:
            print("[OK] Ollama já está ativo.")
            return True
    except Exception:
        pass
    print("[WARN] Ollama não respondendo, iniciando serviço...")
    cmd_str = os.getenv("OLLAMA_COMMAND", "ollama serve")
    import shlex
    cmd = shlex.split(cmd_str)
    _start_service("Ollama", cmd)
    return False

def ensure_litert_running():
    base_url = os.getenv("LITERT_BASE_URL", "http://localhost:9379")
    health_url = _get_health_url(base_url, "http://localhost:9379", "/v1/models")
    try:
        resp = httpx.get(health_url, timeout=2.0)
        if resp.status_code in [200, 404, 401, 405]:
            print("[OK] LiteRT já está ativo.")
            return True
    except Exception:
        pass
    print("[WARN] LiteRT não respondendo, iniciando serviço...")
    cmd_str = os.getenv("LITERT_COMMAND", "litert --serve")
    import shlex
    cmd = shlex.split(cmd_str)
    _start_service("LiteRT", cmd)
    return False

def run_startup_health_checks():
    """Executa verificações de saúde na inicialização do Sentinela.
    - Avalia credenciais Instagram.
    - Garante que Ollama e LiteRT estejam operacionais.
    """
    print("Executando verificações de saúde na inicialização...")
    ig_status = check_instagram_accounts()
    for acc, st in ig_status.items():
        print(f"[IG] {acc}: {st}")
    ensure_ollama_running()
    ensure_litert_running()
