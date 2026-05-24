"""
PASA v50 - Watchdog: Guardião Inteligente com Dashboard Web Live
Diferencia erros de código de erros de runtime, aplica autocura 
e transmite tudo via SSE para o Dashboard.
"""
import time
import subprocess
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

import os
import requests
import json
import asyncio
from threading import Thread, Lock
from typing import Tuple, Dict, Any, Optional

WATCHDOG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(WATCHDOG_DIR)
sys.path.insert(0, WATCHDOG_DIR)
sys.path.insert(0, PROJECT_ROOT)

# Carrega variáveis do arquivo .env local do projeto
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

try:
    from core.auto_updater import check_for_updates
except ImportError:
    check_for_updates = lambda: False

# --- FastAPI Imports ---
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Configurações ---
SERVER_SCRIPT = "main_runner.py"
RESTART_DELAY = 30
REQUIREMENTS_FILE = "requirements.txt"

import tempfile
CACHE_DIR = os.path.join(tempfile.gettempdir(), "sentinela_pip_cache")
TEMP_DIR = os.path.join(tempfile.gettempdir(), "sentinela_tmp")

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

CHILD_ENV = os.environ.copy()
CHILD_ENV["PIP_CACHE_DIR"] = CACHE_DIR
CHILD_ENV["TMP"] = TEMP_DIR
CHILD_ENV["TEMP"] = TEMP_DIR
CHILD_ENV["PYTHONIOENCODING"] = "utf-8"
CHILD_ENV["PYTHONUTF8"] = "1"

CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "558496066876")
CALLMEBOT_APIKEY = os.getenv("CALLMEBOT_APIKEY", "8552672")
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"

CODE_ERRORS = [
    "importerror", "modulenotfounderror", "syntaxerror",
    "indentationerror", "attributeerror", "nameerror", "typeerror",
    "valueerror", "keyerror", "exception", # Erros de config/.env
]

# --- Anti-Spam Categorizado ---
ALERT_COOLDOWNS = {
    "runtime": 3600,  # 1 alerta por hora
    "code": 3600,     # 1 alerta por hora
    "oom": 86400      # 1 alerta por dia
}
last_alert_times = {k: 0.0 for k in ALERT_COOLDOWNS}

# --- Estado Global Compartilhado (Thread-Safe) ---
class WatchdogState:
    def __init__(self):
        self.lock = Lock()
        self.restarts = 0
        self.code_errors = 0
        self.alerts = 0
        self.status = "OPERACIONAL"
        self.logs = []
        self.clients = []
        self.fast_crashes = 0
        
    def add_log(self, level: str, message: str):
        prefix = "" if level == "dim" else f"[{level.upper()}] "
        try:
            print(f"[{time.strftime('%H:%M')}] {prefix}{message}")
        except UnicodeEncodeError:
            try:
                print(f"[{time.strftime('%H:%M')}] {prefix}{message.encode('ascii', 'replace').decode('ascii')}")
            except Exception:
                pass
        with self.lock:
            log_entry = {"time": time.strftime("%H:%M:%S"), "level": level, "message": message}
            self.logs.append(log_entry)
            if len(self.logs) > 200:
                self.logs.pop(0)
            for queue in self.clients:
                try:
                    queue.put_nowait(log_entry)
                except (asyncio.QueueFull, AttributeError):
                    pass
                    
    def update_metrics(self, **kwargs):
        with self.lock:
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)

state = WatchdogState()

# =========================================================
# FASTAPI SERVER (Roda em Thread Separada)
# =========================================================
app = FastAPI(title="Watchdog Dashboard")

# Adicionar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve o dashboard HTML."""
    html_path = os.path.join(PROJECT_ROOT, "local_dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content=f"<h1>Dashboard não encontrado em {html_path}</h1>", status_code=404)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Retorna o favicon do projeto para evitar erro 404."""
    favicon_path = os.path.join(PROJECT_ROOT, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/api/stream")
async def stream(request: Request):
    """Server-Sent Events para logs em tempo real com MIME Type corrigido."""
    queue = asyncio.Queue(maxsize=100)
    
    with state.lock:
        state.clients.append(queue)
        # Envia logs históricos (últimos 50)
        for log in state.logs[-50:]:
            try:
                queue.put_nowait(log)
            except asyncio.QueueFull:
                pass
            
    async def event_generator():
        try:
            while True:
                # Verifica se cliente desconectou
                if await request.is_disconnected():
                    break
                
                try:
                    # Aguarda novo log (timeout 30s)
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    
                except asyncio.TimeoutError:
                    # Envia keepalive para manter conexão viva
                    yield ": keepalive\n\n"
                    
        except asyncio.CancelledError:
            pass  # Cliente desconectou normalmente
        finally:
            # Remove cliente da lista
            with state.lock:
                if queue in state.clients:
                    state.clients.remove(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",  # ✅ Tipo MIME correto
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.get("/api/metrics")
async def get_metrics():
    """Endpoint para métricas atualizadas via Supabase (v55.3)."""
    worker_metrics = {"queue_size": 0, "cycle": 0, "level": 1, "trust": 0.0, "tier": "silver", "score": 0.0}
    try:
        from workers.base.memory_store import MemoryStore
        store = MemoryStore()
        recent = await store.get_recent("ig-v2-01", n=1)
        if recent:
            last = recent[0]
            worker_metrics = {
                "queue_size": 0, # Fila dinâmica via Supabase
                "cycle": last.cycle,
                "level": 4 if last.tier == 'platinum' else (3 if last.tier == 'gold' else 2),
                "trust": last.score / 10.0,
                "tier": last.tier,
                "score": last.score
            }
    except Exception as e:
        state.add_log("dim", f"[Watchdog] Erro ao carregar métricas Supabase: {e}")
    
    with state.lock:
        return {
            "restarts": state.restarts,
            "code_errors": state.code_errors,
            "alerts": state.alerts,
            "status": state.status,
            "fast_crashes": state.fast_crashes,
            "db_status": "OPERACIONAL",
            **worker_metrics
        }

def run_web_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")  

# =========================================================
# WATCHDOG CORE LOGIC
# =========================================================

def get_python_executable() -> str:
    # Se o watchdog foi iniciado por um executável Python válido, usamos ele
    # para herdar o ambiente correto (como o ambiente virtual gerenciado por 'uv')
    if sys.executable and os.path.exists(sys.executable):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Se estamos sob uv run ou venv ativo, sys.prefix difere ou detectamos uv pelo executável
        if "uv" in sys.executable.lower() or sys.prefix != sys.base_prefix:
            return sys.executable
            
        venv_paths = [
            os.path.join(project_root, ".venv", "Scripts", "python.exe"),
            os.path.join(project_root, "venv", "Scripts", "python.exe"),
            os.path.join(project_root, ".venv", "bin", "python"),
            os.path.join(project_root, "venv", "bin", "python"),
        ]
        for path in venv_paths:
            # Verifica se o venv existe E se ele é um ambiente íntegro (com pip funcional no mesmo diretório)
            if os.path.exists(path):
                bin_dir = os.path.dirname(path)
                pip_name = "pip.exe" if sys.platform.startswith("win") else "pip"
                if os.path.exists(os.path.join(bin_dir, pip_name)):
                    return path
        return sys.executable
    return sys.executable

def classify_error(stderr_output: str) -> str:
    if not stderr_output:
        return "runtime"
    stderr_lower = stderr_output.lower()
    for err_type in CODE_ERRORS:
        if err_type in stderr_lower:
            return "code"
    return "runtime"

def heal_dependencies(python_exe: str) -> None:
    state.add_log("info", "[Watchdog] Verificando integridade das dependências...")
    try:
        subprocess.run(
            [python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE, "-q"],
            check=True, env=CHILD_ENV,
        )
        state.add_log("info", "[Watchdog] Dependências sincronizadas.")
    except subprocess.CalledProcessError:
        state.add_log("warn", "[Watchdog] Falha na instalação. Purgando cache...")
        try:
            subprocess.run([python_exe, "-m", "pip", "cache", "purge"], check=True, env=CHILD_ENV)
            subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE, "-q"],
                check=True, env=CHILD_ENV,
            )
            state.add_log("info", "[Watchdog] Dependências sincronizadas após purga.")
        except Exception as e2:
            state.add_log("error", f"[Watchdog] Falha crítica ao curar dependências: {e2}")

def send_whatsapp_alert(message: str, category: str = "runtime") -> None:
    global last_alert_times
    now = time.time()
    cooldown = ALERT_COOLDOWNS.get(category, 1800)
    
    if now - last_alert_times.get(category, 0) < cooldown:
        state.add_log("dim", f"[Watchdog] Alerta '{category}' suprimido (cooldown {cooldown//60}m).")
        return
    
    try:
        params = {"phone": CALLMEBOT_PHONE, "apikey": CALLMEBOT_APIKEY, "text": message}
        requests.get(CALLMEBOT_URL, params=params, timeout=10)
        last_alert_times[category] = now
        state.update_metrics(alerts=state.alerts + 1)
        state.add_log("info", f"[Watchdog] 📲 Alerta WhatsApp ({category}) enviado.")
    except Exception as e:
        state.add_log("error", f"[Watchdog] Falha ao enviar alerta: {e}")

def heal_runtime_error(reason: str) -> str:
    stderr_lower = reason.lower()
    
    if "out of memory" in stderr_lower or "oom-killer" in stderr_lower or "cannot allocate memory" in stderr_lower:
        state.add_log("error", "[Watchdog] 🛑 OOM Detectado! Reinícios parados para proteger o sistema.")
        state.update_metrics(status="PARADO - OOM")
        return "fatal"
        
    if "connectionrefusederror" in stderr_lower or "supabase" in stderr_lower:
        state.add_log("warn", "[Watchdog] ⏸️ Banco de dados/API offline. Aguardando 5 min antes de tentar.")
        time.sleep(300)
        return "wait"
        
    if "browser closed" in stderr_lower or "playwright" in stderr_lower:
        state.add_log("warn", "[Watchdog] 🧹 Playwright detectado nos logs de erro. Limpando processos órfãos...")
        try:
            if os.name == 'nt':
                subprocess.run(["taskkill", "/F", "/IM", "chromium.exe"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", "chromium"], capture_output=True)
        except Exception:
            pass
        return "restart"
        
    return "restart"

def guard():
    python_exe = get_python_executable()
    consecutive_code_errors = 0

    while True:
        # 1. Auto Update
        try:
            if check_for_updates():
                heal_dependencies(python_exe)
        except Exception:
            pass

        # 2. Executar Servidor
        state.update_metrics(status="OPERACIONAL")
        state.add_log("info", "[Watchdog] Iniciando main_runner.py...")
        try:
            ENV_WITH_WATCHDOG = CHILD_ENV.copy()
            ENV_WITH_WATCHDOG["WATCHDOG_ACTIVE"] = "true"
            ENV_WITH_WATCHDOG["PYTHONUNBUFFERED"] = "1"

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            process = subprocess.Popen(
                [python_exe, "-u", SERVER_SCRIPT],
                env=ENV_WITH_WATCHDOG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=project_root,
            )
            
            def pipe_reader(pipe, level):
                NOISY_PATTERNS = ["HTTP Request:", "HTTP/2 200 OK", "HTTP/2 201 Created"]
                for line in iter(pipe.readline, ''):
                    clean_line = line.strip()
                    if clean_line:
                        if any(pattern in clean_line for pattern in NOISY_PATTERNS):
                            continue
                        log_level = level
                        upper_line = clean_line.upper()
                        if "ERROR" in upper_line or "❌" in clean_line: log_level = "error"
                        elif "WARN" in upper_line or "⚠️" in clean_line: log_level = "warn"
                        elif "✅" in clean_line or "🚀" in clean_line: log_level = "info"
                        state.add_log(log_level, clean_line)
                pipe.close()

            t_stdout = Thread(target=pipe_reader, args=(process.stdout, "dim"), daemon=True)
            t_stderr = Thread(target=pipe_reader, args=(process.stderr, "error"), daemon=True)
            t_stdout.start()
            t_stderr.start()

            while True:
                poll = process.poll()
                if poll is not None:
                    break
                time.sleep(2)

            t_stdout.join(timeout=5)
            t_stderr.join(timeout=5)

            if poll != 0:
                error_type = "runtime"
                with state.lock:
                    recent_logs = "".join([l["message"] for l in state.logs[-10:]]).lower()
                    for err_type in CODE_ERRORS:
                        if err_type in recent_logs:
                            error_type = "code"
                            break
                
                if error_type == "code":
                    consecutive_code_errors += 1
                    state.update_metrics(code_errors=consecutive_code_errors)
                    state.add_log("error", f"[Watchdog] ⛔ ERRO DE CÓDIGO detectado (tentativa {consecutive_code_errors})")
                    
                    if consecutive_code_errors >= 3:
                        send_whatsapp_alert("🛑 *WATCHDOG: ERRO DE CÓDIGO* 🛑\nReinícios parados. Correção manual necessária.", category="code")
                        state.update_metrics(status="PARADO - ERRO CODIGO")
                        state.add_log("error", "[Watchdog] 🛑 3 erros consecutivos. Parando.")
                        break
                    elif consecutive_code_errors == 1:
                        heal_dependencies(python_exe)
                else:
                    consecutive_code_errors = 0
                    state.update_metrics(restarts=state.restarts + 1)
                    state.add_log("warn", "[Watchdog] ⚠️ Falha rápida na inicialização. Analisando autocura...")
                    
                    healing_action = heal_runtime_error(recent_logs or "erro desconhecido")
                    
                    if healing_action == "fatal":
                        send_whatsapp_alert("🛑 *WATCHDOG: OOM FATAL* 🛑\nMemória esgotada. Sistema pausado.", category="oom")
                        break
                    
                    state.fast_crashes += 1
                    
                    if state.fast_crashes >= 3:
                        state.add_log("error", "[Watchdog] 🛑 3 falhas rápidas consecutivas. Hibernando por 1h.")
                        send_whatsapp_alert("⚠️ *WATCHDOG: INIT LOOP* ⚠️\nServidor falhou ao iniciar 3x. Hibernando 1h.", category="runtime")
                        state.update_metrics(status="HIBERNANDO - INIT LOOP")
                        time.sleep(3600)
                        state.fast_crashes = 0
                    else:
                        send_whatsapp_alert(f"🚨 *WATCHDOG: RUNTIME ERROR* 🚨\nCode: {poll}. Reiniciando.", category="runtime")
            else:
                consecutive_code_errors = 0
                state.fast_crashes = 0
                state.update_metrics(code_errors=0)
                
        except KeyboardInterrupt:
            state.add_log("dim", "[Watchdog] Interrompido pelo operador.")
            break
        except Exception as e:
            state.add_log("error", f"[Watchdog] Exceção no guardião: {e}")
        
        delay = RESTART_DELAY * min(consecutive_code_errors + 1, 5)
        state.add_log("dim", f"[Watchdog] Aguardando {delay}s antes do próximo ciclo...")
        time.sleep(delay)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("[START] Dashboard disponível em: http://localhost:8001")
    print("[SHIELD] SENTINELA DEMOCRÁTICA - WATCHDOG v50.0")
    guard()
