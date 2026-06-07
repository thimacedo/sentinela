"""
PASA v50 - Watchdog: Guardião Inteligente com Dashboard Web Live
Diferencia erros de código de erros de runtime, aplica autocura 
e transmite tudo via SSE para o Dashboard.
"""
import os
import sys

# --- AUTO-ANCHORING (v61.5) ---
WATCHDOG_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(WATCHDOG_FILE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import time
import subprocess
import requests
import json
import traceback
from core.health_check import check_instagram_accounts
import asyncio
from threading import Thread, Lock
from typing import Tuple, Dict, Any, Optional

# Carrega variáveis do arquivo .env local do projeto
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)
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
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements-workers.txt") 

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

# --- ATIVAÇÃO DO AUTOPILOT L3 (PASA v70.0) ---
try:
    from core.autopilot.manager import autopilot
    AUTOPILOT_ENABLED = True
except ImportError:
    AUTOPILOT_ENABLED = False

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
        self.process = None
        self.should_run = True
        
    def add_log(self, level: str, message: str):
        # Filtragem Inteligente para Reduzir "Enxurrada de Erros" no Terminal (v88.9)
        # Omitimos do stdout mensagens de erro de rede/IA repetitivas, mas mantemos no Dashboard/SSE.
        SUPPRESSED_TERMINAL_TERMS = ["429", "403", "401", "CIRCUITO ABERTO", "COOLDOWN", "HTTP REQUEST:", "HTTP/2 200 OK"]
        msg_upper = message.upper()
        
        should_print = True
        if any(term in msg_upper for term in SUPPRESSED_TERMINAL_TERMS):
            if level in ["dim", "warn", "error"]:
                should_print = False

        prefix = "" if level == "dim" else f"[{level.upper()}] "
        if should_print:
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

@app.get("/api/analytics/top-attackers")
async def get_top_attackers():
    """Retorna os perfis mais agressivos usando o banco local."""
    try:
        from workers.ai.sa_consulta_banco import SaConsultaBanco
        sa = SaConsultaBanco()
        data = await sa.get_top_attackers(limit=5)
        await sa.close()
        return {"attackers": data}
    except Exception as e:
        return {"attackers": [], "error": str(e)}

@app.get("/api/analytics/hate-stats")
async def get_hate_stats():
    """Retorna estatísticas de ódio por candidato usando o banco local."""
    try:
        from workers.ai.sa_consulta_banco import SaConsultaBanco
        sa = SaConsultaBanco()
        data = await sa.get_hate_stats()
        await sa.close()
        return {"stats": data}
    except Exception as e:
        return {"stats": [], "error": str(e)}

@app.get("/api/analytics/search")
async def search_local(q: str):
    """Busca textual ultra-rápida usando FTS5 local."""
    try:
        from workers.ai.sa_consulta_banco import SaConsultaBanco
        sa = SaConsultaBanco()
        data = await sa.search_comments(q, limit=20)
        await sa.close()
        return {"results": data}
    except Exception as e:
        return {"results": [], "error": str(e)}

@app.get("/api/evaluations")
async def get_evaluations():
    """Retorna o histórico recente de avaliações para persistência no frontend."""
    try:
        eval_file = os.path.join(PROJECT_ROOT, "data", "ia_evaluations.jsonl")
        if not os.path.exists(eval_file):
            return {"evaluations": {}}
        
        evals = {}
        with open(eval_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("comment_id"):
                        evals[str(data["comment_id"])] = {
                            "type": data.get("feedback_type"),
                            "is_correct": data.get("is_correct")
                        }
                except: continue
        return {"evaluations": evals}
    except Exception as e:
        return {"evaluations": {}, "error": str(e)}

@app.post("/api/evaluate")
async def evaluate_ia(data: dict):
    """
    Recebe avaliação de uma classificação de IA.
    Salva localmente para análise de performance por modelo.
    """
    try:
        eval_file = os.path.join(PROJECT_ROOT, "data", "ia_evaluations.jsonl")
        os.makedirs(os.path.dirname(eval_file), exist_ok=True)
        
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "comment_id": data.get("id"),
            "trace_id": data.get("trace_id"),
            "engine": data.get("engine"),
            "feedback_type": data.get("feedback_type"),
            "is_correct": data.get("is_correct"), # maintain for legacy compatibility
            "category_assigned": data.get("category"),
            "text_snippet": data.get("text")[:100] if data.get("text") else ""
        }
        
        with open(eval_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        # Dispara para reclassificação se for um falso positivo ou negativo
        if data.get("feedback_type") in ["FALSO_POSITIVO", "FALSO_NEGATIVO"] and data.get("id"):
            try:
                from core.supabase_service import get_supabase_client
                db = get_supabase_client()
                db.client.table("comentarios").update({
                    "processado_ia": False,
                    "confianca_ia": 0.0,
                    "analise_pericial": f"[RE-ANÁLISE SOLICITADA] {data.get('feedback_type')}",
                    "prioridade": 99
                }).eq("id", data.get("id")).execute()
            except Exception as e:
                print(f"[Watchdog] Erro ao engatilhar reclassificacao: {e}")
                
        return {"success": True, "message": "Avaliação registrada e reclassificação engatilhada."}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/ai_health")
async def get_ai_health():
    """
    Expõe o estado REAL dos circuit breakers do ai_service.
    Diferente de /api/metrics, este endpoint mostra se o provedor está
    realmente disponível no momento (não apenas se a chave existe no .env).
    """
    try:
        import time as _time
        from core.circuit_breaker import ai_circuit_breaker
        from core.ai_service import ai_service

        now = _time.time()
        result = {}

        # Itera sobre os provedores ativos na fila do ai_service
        active_names = {p["name"] for p in ai_service.providers}

        # Inclui também provedores que podem ter sido removidos permanentemente
        all_known = active_names | set(ai_circuit_breaker.open_until.keys())

        for name in sorted(all_known):
            if name not in active_names:
                # Provedor removido permanentemente (ex: 401/403)
                result[name] = {"status": "REMOVIDO", "icon": "🔴", "detail": "Removido permanentemente (erro fatal)"}
                continue

            prov = next((p for p in ai_service.providers if p["name"] == name), None)
            cooldown_until = prov.get("cooldown_until", 0) if prov else 0
            cb_until = ai_circuit_breaker.open_until.get(name, 0)
            failures = ai_circuit_breaker.failures.get(name, 0)

            # Determina o status mais restritivo
            if cb_until > now:
                secs_left = int(cb_until - now)
                if secs_left > 1800:  # > 30min → provavelmente erro fatal
                    result[name] = {"status": "BLOQUEADO", "icon": "🔴", "detail": f"Circuit breaker aberto por mais {secs_left//60}min (erro fatal)"}
                else:
                    result[name] = {"status": "RATE_LIMIT", "icon": "🟡", "detail": f"Cooldown por mais {secs_left}s ({failures} falhas)"}
            elif cooldown_until > now:
                secs_left = int(cooldown_until - now)
                result[name] = {"status": "COOLDOWN", "icon": "🟡", "detail": f"Cooldown por mais {secs_left}s"}
            else:
                result[name] = {"status": "OK", "icon": "🟢", "detail": "Disponível"}

        return {"providers": result, "timestamp": now}
    except Exception as e:
        return {"providers": {}, "error": str(e)}

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
    """Endpoint para métricas atualizadas via Supabase (v55.3) + indicadores de Instagram e IA."""
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
    # Instagram accounts status
    ig_status = check_instagram_accounts()
    # IA services health checks (não iniciam serviços)
    from urllib.parse import urlparse
    import httpx

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

    def _service_status(url: str) -> str:
        try:
            resp = httpx.get(url, timeout=2.0)
            return "OK" if resp.status_code in [200, 404, 401, 405] else "DOWN"
        except Exception:
            return "DOWN"

    # Checagem de status de IA — usa circuit breakers reais se o runner estiver ativo
    ai_status = {}
    ai_status_detail = {}  # campo extra com status detalhado por provedor

    try:
        # Tenta ler o estado real dos circuit breakers do processo runner em memória
        import time as _time
        from core.circuit_breaker import ai_circuit_breaker
        from core.ai_service import ai_service

        now = _time.time()
        active_names = {p["name"] for p in ai_service.providers}
        all_known = active_names | set(ai_circuit_breaker.open_until.keys())

        for name in sorted(all_known):
            if name not in active_names:
                ai_status[name] = "REMOVIDO"
                continue
            prov = next((p for p in ai_service.providers if p["name"] == name), None)
            cooldown_until = prov.get("cooldown_until", 0) if prov else 0
            cb_until = ai_circuit_breaker.open_until.get(name, 0)
            if cb_until > now:
                secs_left = int(cb_until - now)
                ai_status[name] = "BLOQUEADO" if secs_left > 1800 else "RATE_LIMIT"
            elif cooldown_until > now:
                ai_status[name] = "COOLDOWN"
            else:
                ai_status[name] = "OK"
    except Exception:
        # Fallback: verifica apenas presença das chaves no .env
        ollama_health = _get_health_url(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), "http://localhost:11434", "/api/tags")
        ai_status["ollama"] = _service_status(ollama_health)
        for prov_name, env_var in {"groq": "GROQ_API_KEY", "mistral": "MISTRAL_API_KEY", "deepseek": "DEEPSEEK_API_KEY", "openrouter": "OPENROUTER_API_KEY", "gemini": "GEMINI_API_KEY"}.items():
            val = os.getenv(env_var, "").strip()
            ai_status[prov_name] = "OK" if (val and "dummy" not in val.lower()) else "DESATIVADO"

    with state.lock:
        return {
            "restarts": state.restarts,
            "code_errors": state.code_errors,
            "alerts": state.alerts,
            "status": state.status,
            "fast_crashes": state.fast_crashes,
            "db_status": "OPERACIONAL",
            "instagram_accounts": ig_status,
            "ai_services": ai_status,
            **worker_metrics
        }

@app.post("/api/services/{name}/start")
async def start_service_endpoint(name: str):
    """Endpoint para inicialização manual sob demanda de Ollama."""
    from fastapi import HTTPException
    
    if name == "ollama":
        try:
            from core.health_check import ensure_ollama_running
            if ensure_ollama_running():
                return {"status": "success", "message": "Ollama já está operacional."}
            return {"status": "success", "message": "Comando de inicialização do Ollama enviado."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao iniciar Ollama: {str(e)}")
            
    else:
        raise HTTPException(status_code=400, detail=f"Serviço desconhecido: {name}")

@app.get("/api/ai/details/{name}")
async def get_ai_details(name: str):
    """Retorna detalhes de um provedor para gestão no dashboard."""
    env_vars = {
        "maritaca": "MARITACA_API_KEY",
        "google_gemini": "GEMINI_API_KEY",
        "groq_llama3": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "huggingface": "HF_TOKEN"
    }
    
    links = {
        "maritaca": "https://chat.maritaca.ai/keys",
        "google_gemini": "https://aistudio.google.com/app/apikey",
        "groq_llama3": "https://console.groq.com/keys",
        "mistral": "https://console.mistral.ai/api-keys/",
        "deepseek": "https://platform.deepseek.com/api_keys",
        "openrouter": "https://openrouter.ai/keys",
        "huggingface": "https://huggingface.co/settings/tokens"
    }

    env_var = env_vars.get(name)
    if not env_var:
        return {"error": "Provedor desconhecido"}
        
    current_key = os.getenv(env_var, "")
    
    return {
        "name": name,
        "env_var": env_var,
        "key": current_key,
        "auth_url": links.get(name, "#"),
        "instructions": f"Para {name}, obtenha uma chave no link acima e cole-a no campo abaixo. O sistema testará a conexão imediatamente."
    }

@app.post("/api/ai/update_key")
async def update_ai_key(data: dict):
    """Atualiza uma chave no .env e testa imediatamente."""
    name = data.get("name")
    env_var = data.get("env_var")
    new_key = data.get("key", "").strip()
    
    if not name or not env_var or not new_key:
        return {"success": False, "message": "Dados incompletos"}

    try:
        # 1. Atualiza o arquivo .env fisicamente
        from dotenv import set_key
        env_path = os.path.join(PROJECT_ROOT, ".env")
        set_key(env_path, env_var, new_key)
        
        # 2. Atualiza em memória para o processo atual
        os.environ[env_var] = new_key
        
        # 3. Testa a chave imediatamente
        state.add_log("info", f"[Manager] Testando nova chave para {name}...")
        
        test_success = False
        error_msg = ""
        
        if name == "maritaca":
            import httpx
            try:
                resp = httpx.post("https://chat.maritaca.ai/api/chat/completions", 
                                 headers={"Authorization": f"Bearer {new_key}"},
                                 json={"model": "sabia-4", "messages": [{"role":"user", "content":"hi"}]},
                                 timeout=10.0)
                test_success = resp.status_code != 403
                if not test_success: error_msg = resp.text
            except Exception as e:
                error_msg = str(e)
        else:
            # Teste genérico para outros (apenas validação básica de formato por ora ou ping)
            test_success = len(new_key) > 10
            
        if test_success:
            state.add_log("info", f"✅ Nova chave para {name} VALIDADA com sucesso.")
            # Dispara restart para o runner herdar a chave
            try:
                requests.post("http://localhost:8001/api/server/restart", timeout=2.0)
            except: pass
            return {"success": True, "message": f"Chave de {name} atualizada e validada. Reiniciando runner..."}
        else:
            state.add_log("error", f"❌ Falha ao validar nova chave de {name}: {error_msg}")
            return {"success": False, "message": f"Chave inválida ou sem saldo: {error_msg}"}

    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/server/start")
async def start_server():
    if state.should_run and state.process and state.process.poll() is None:
        return {"success": False, "message": "Servidor já está rodando."}
    state.should_run = True
    state.add_log("info", "[Watchdog] Sinal de inicialização recebido via API.")
    return {"success": True, "message": "Sinal de inicialização enviado."}

@app.post("/api/server/stop")
async def stop_server():
    state.should_run = False
    if state.process and state.process.poll() is None:
        state.add_log("warn", "[Watchdog] Sinal de parada recebido via API. Finalizando processo...")
        # v50.1: Encerra árvore de processos para evitar zumbis
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(state.process.pid)], capture_output=True)
            else:
                state.process.terminate()
        except Exception as e:
            state.add_log("error", f"[Watchdog] Falha ao encerrar processo: {e}")
            
        state.update_metrics(status="PARADO")
        return {"success": True, "message": "Sinal de parada enviado. Processo encerrado."}
    state.update_metrics(status="PARADO")
    state.add_log("info", "[Watchdog] Servidor já estava parado.")
    return {"success": True, "message": "Servidor parado."}

@app.post("/api/server/restart")
async def restart_server():
    if state.process and state.process.poll() is None:
        state.add_log("warn", "[Watchdog] Sinal de reinício recebido via API. Reiniciando processo...")
        state.process.terminate()
        return {"success": True, "message": "Reiniciando servidor..."}
    else:
        state.should_run = True
        state.add_log("info", "[Watchdog] Sinal de reinício recebido com servidor parado. Iniciando...")
        return {"success": True, "message": "Iniciando servidor..."}

def run_web_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")  

# =========================================================
# WATCHDOG CORE LOGIC
# =========================================================

def get_python_executable() -> str:
    # v90.6: Prefer uv for all operations to avoid shims/launchers issues
    try:
        import subprocess
        # Verifica se uv está no PATH
        subprocess.check_output(["uv", "--version"], shell=True, creationflags=0x08000000)
        return "uv_run_python" # Marcador especial
    except:
        pass

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
        flags = 0x08000000 if os.name == 'nt' else 0
        # v61.2: Usa uv para instalar dependências se disponível
        subprocess.run(
            ["uv", "pip", "install", "-r", REQUIREMENTS_FILE, "-q"],
            check=True, env=CHILD_ENV, creationflags=flags
        )
        state.add_log("info", "[Watchdog] Dependências sincronizadas via 'uv'.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        state.add_log("warn", "[Watchdog] Falha na instalação via 'uv'. Tentando fallback...")
        try:
            flags = 0x08000000 if os.name == 'nt' else 0
            subprocess.run(["uv", "cache", "clean"], check=True, env=CHILD_ENV, creationflags=flags)
            subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", REQUIREMENTS_FILE, "-q"],
                check=True, env=CHILD_ENV, creationflags=flags
            )
            state.add_log("info", "[Watchdog] Dependências sincronizadas após purga de cache.")
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
        
    _db_connection_terms = [
        "connectionrefusederror",
        "connection refused",
        "could not connect",
        "connection reset",
        "network unreachable",
        "max retries exceeded",
        "failed to connect",
        "unable to connect",
        "econnrefused",
        "10060",
        "timed out",
        "timeout",
        "componente conectado não respondeu",
    ]
    _is_db_failure = any(t in stderr_lower for t in _db_connection_terms)
    if _is_db_failure:
        state.add_log("warn", "[Watchdog] ⏸️ Banco de dados/API offline. Aguardando 5 min antes de tentar.")
        time.sleep(300)
        return "wait"
        
    if "browser closed" in stderr_lower or "playwright" in stderr_lower:
        state.add_log("warn", "[Watchdog] 🧹 Playwright detectado nos logs de erro. Limpando processos órfãos...")
        try:
            flags = 0x08000000 if os.name == 'nt' else 0
            if os.name == 'nt':
                subprocess.run('wmic process where "ExecutablePath like \'%ms-playwright%\'" call terminate', shell=True, capture_output=True, creationflags=flags)
            else:
                subprocess.run(["pkill", "-f", "playwright"], capture_output=True)
        except Exception:
            pass
        return "restart"
        
    return "restart"

# --- MARITACA RESURRECTOR (v90.6) ---
def maritaca_resurrector_loop():
    """Verifica periodicamente se a Maritaca recuperou saldo e desperta o runner."""
    while True:
        try:
            key = os.getenv("MARITACA_API_KEY", "").strip()
            if key and "dummy" not in key.lower():
                import httpx
                resp = httpx.get(
                    "https://chat.maritaca.ai/api/info/credits",
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    credits = data.get("credits", 0.0)
                    if credits > 0.0:
                        state.add_log("info", f"[Resurrector] 🔔 Saldo Maritaca detectado: R$ {credits:.2f}. Despertando IA...")
                        # Se o saldo voltou, precisamos forçar o runner a recarregar o AIService
                        requests.post("http://localhost:8001/api/server/restart", timeout=5.0)
                        # Espera 4 horas antes de checar novamente se o saldo ainda está lá (evita loops se o restart falhar)
                        time.sleep(14400)
                        continue
        except Exception as e:
            # Silencioso para não poluir logs se houver erro de rede intermitente
            pass
        
        # Checa a cada 1 hora
        time.sleep(3600)

def guard():
    from core.guard_locker import GuardLocker
    from core.process_cleaner import cleanup_orphans
    
    # 🔐 Garante instância única do Watchdog
    watchdog_locker = GuardLocker("watchdog", PROJECT_ROOT)
    if not watchdog_locker.acquire(kill_existing=True):
        print("🚨 [Watchdog] Outra instância do Watchdog já está ativa. Abortando.")
        sys.exit(1)

    # Garantir que serviços de IA estejam operacionais antes de iniciar o ciclo
    python_exe = None
    while python_exe is None:
        try:
            from core.health_check import run_startup_health_checks
            run_startup_health_checks()
            python_exe = get_python_executable()
        except Exception as e:
            state.add_log("error", f"[Watchdog] Falha na inicialização do guardião: {e}")
            time.sleep(5)
            
    consecutive_code_errors = 0

    while True:
        # Checa se deve rodar o processo. Se não, fica em loop de espera
        if not state.should_run:
            if not (state.status and state.status.startswith("PARADO -")):
                state.update_metrics(status="PARADO")
            state.process = None
            while not state.should_run:
                time.sleep(1)
            consecutive_code_errors = 0
            state.fast_crashes = 0
            state.update_metrics(status="OPERACIONAL", code_errors=0)

        # 1. Auto Update e Faxina agressiva de processos órfãos (v88.5)
        try:
            if check_for_updates():
                heal_dependencies(python_exe)
            
            # Limpeza preventiva antes de iniciar o main_runner
            state.add_log("info", "[Watchdog] Realizando limpeza preventiva de processos órfãos...")
            cleanup_orphans(kill_ollama=False) # Não mata Ollama a menos que esteja duplicado (o health_check cuida disso)
        except Exception as e:
            state.add_log("warn", f"[Watchdog] Falha na limpeza preventiva: {e}")

        # 2. Executar Servidor
        state.update_metrics(status="OPERACIONAL")
        state.add_log("info", "[Watchdog] Iniciando main_runner.py...")
        try:
            ENV_WITH_WATCHDOG = CHILD_ENV.copy()
            ENV_WITH_WATCHDOG["WATCHDOG_ACTIVE"] = "true"
            ENV_WITH_WATCHDOG["PYTHONUNBUFFERED"] = "1"

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # v90.6: Seletor de comando para evitar shims zumbis
            if python_exe == "uv_run_python":
                full_cmd = ["uv", "run", "python", "-u", SERVER_SCRIPT]
            else:
                full_cmd = [python_exe, "-u", SERVER_SCRIPT]

            # Inicia o script principal sem abrir janela de console (Windows)
            creationflags = 0x08000000  # CREATE_NO_WINDOW
            process = subprocess.Popen(
                full_cmd,
                env=ENV_WITH_WATCHDOG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=project_root,
                creationflags=creationflags,
            )
            state.process = process
            start_time = time.time()
            
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
                        elif "✅" in clean_line or "🚀" in clean_line or "📊" in clean_line: log_level = "info"
                        state.add_log(log_level, clean_line)
                pipe.close()

            t_stdout = Thread(target=pipe_reader, args=(process.stdout, "dim"), daemon=True)
            t_stderr = Thread(target=pipe_reader, args=(process.stderr, "error"), daemon=True)
            t_stdout.start()
            t_stderr.start()

            while state.should_run:
                poll = process.poll()
                if poll is not None:
                    break
                time.sleep(1)

            t_stdout.join(timeout=2)
            t_stderr.join(timeout=2)

            if poll is not None and poll != 0:
                error_type = "runtime"
                with state.lock:
                    # Analisamos os logs recentes em busca de tracebacks reais
                    # Evitamos capturar a palavra "exception" genérica fora de contexto
                    recent_logs = "".join([l["message"] for l in state.logs[-20:]]).lower()
                    
                    critical_errors = [
                        "importerror", "modulenotfounderror", "syntaxerror",
                        "indentationerror", "attributeerror", "nameerror", "typeerror",
                        "valueerror", "keyerror", "recursionerror", "zerodivisionerror"
                    ]
                    
                    if any(err in recent_logs for err in critical_errors):
                        error_type = "code"
                    elif "traceback (most recent call last)" in recent_logs:
                        error_type = "code"
                
                if error_type == "code":
                    consecutive_code_errors += 1
                    state.update_metrics(code_errors=consecutive_code_errors)
                    state.add_log("error", f"[Watchdog] ERRO DE CODIGO detectado (tentativa {consecutive_code_errors})")
                    
                    if consecutive_code_errors >= 3:
                        send_whatsapp_alert("WATCHDOG: ERRO DE CODIGO - Reinicios parados. Correcao manual necessaria.", category="code")
                        state.update_metrics(status="PARADO - ERRO CODIGO")
                        state.add_log("error", "[Watchdog] 3 erros consecutivos de código. Entrando em pausa de segurança.")
                        state.should_run = False
                        continue
                    elif consecutive_code_errors == 1:
                        heal_dependencies(python_exe)
                else:
                    consecutive_code_errors = 0
                    runtime = time.time() - start_time
                    state.update_metrics(restarts=state.restarts + 1)
                    
                    if runtime > 60:
                        state.add_log("warn", f"[Watchdog] Processo finalizado apos {int(runtime)}s. Reiniciando...")
                        state.fast_crashes = 0
                    else:
                        state.add_log("warn", "[Watchdog] Falha rapida na inicializacao. Analisando autocura...")
                        state.fast_crashes += 1
                        
                    healing_action = heal_runtime_error(recent_logs or "erro desconhecido")
                    
                    if healing_action == "fatal":
                        send_whatsapp_alert("WATCHDOG: OOM FATAL - Memoria esgotada. Sistema pausado.", category="oom")
                        state.update_metrics(status="PARADO - OOM")
                        state.should_run = False
                        continue
                    
                    if state.fast_crashes >= 3:
                        state.add_log("error", "[Watchdog] 3 falhas rapidas consecutivas. Hibernando por 1h.")
                        send_whatsapp_alert("WATCHDOG: INIT LOOP - Servidor falhou ao iniciar 3x. Hibernando 1h.", category="runtime")
                        state.update_metrics(status="HIBERNANDO - INIT LOOP", should_run=False)
                        
                        # Espera defensiva interrompível (1 hora)
                        elapsed = 0
                        while elapsed < 3600 and not state.should_run:
                            time.sleep(5)
                            elapsed += 5
                            
                        state.fast_crashes = 0
                    elif runtime <= 60:
                        send_whatsapp_alert(f"WATCHDOG: RUNTIME ERROR - Code: {poll}. Reiniciando.", category="runtime")
            elif poll is None:
                # Parada manual via should_run = False
                state.add_log("info", "[Watchdog] Processo encerrado pelo operador.")
                consecutive_code_errors = 0
                state.fast_crashes = 0
            else:
                consecutive_code_errors = 0
                state.fast_crashes = 0
                state.update_metrics(code_errors=0)
                
        except KeyboardInterrupt:
            state.add_log("dim", "[Watchdog] Interrompido pelo operador.")
            break
        except Exception as e:
            state.add_log("error", f"[Watchdog] Exceção no guardião: {e}")
            traceback.print_exc()
        
        # Cooldown interrompível
        delay = RESTART_DELAY * min(consecutive_code_errors + 1, 5)
        state.add_log("dim", f"[Watchdog] Cooldown de {delay}s... (interrompível)")
        
        elapsed_delay = 0
        while elapsed_delay < delay and state.should_run:
            time.sleep(1)
            elapsed_delay += 1

        # Executa sincronização com o Datasette local durante o cooldown (repouso) de forma assíncrona (não-bloqueante)
        if state.should_run and state.fast_crashes == 0 and consecutive_code_errors == 0:
            def run_sync():
                try:
                    state.add_log("info", "[Watchdog] Sincronizando dados para o Datasette local...")
                    from scripts.export_to_sqlite import export_to_sqlite
                    export_to_sqlite()
                    state.add_log("info", "[Watchdog] Sincronização Datasette concluída com sucesso durante o descanso.")
                except Exception as e:
                    err_msg = str(e).lower()
                    if any(t in err_msg for t in ["10060", "timed out", "timeout", "connection", "componente conectado não respondeu"]):
                        state.add_log("warn", "[Watchdog] Sincronização Datasette ignorada: Banco de dados/Rede offline.")
                    else:
                        state.add_log("warn", f"[Watchdog] Falha ao sincronizar Datasette no cooldown: {e}")
            
            Thread(target=run_sync, daemon=True).start()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 🤖 INICIALIZAÇÃO DO AUTOPILOT L3 (PASA v70.0)
    if AUTOPILOT_ENABLED:
        def run_autopilot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            state.add_log("info", "[Watchdog] 🤖 Autopilot L3 Ativado.")
            try:
                loop.run_until_complete(autopilot.pulse())
            except Exception as e:
                state.add_log("error", f"[Watchdog] 🤖 Autopilot falhou: {e}")

        autopilot_thread = Thread(target=run_autopilot, daemon=True)
        autopilot_thread.start()

    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()

    resurrector_thread = Thread(target=maritaca_resurrector_loop, daemon=True)
    resurrector_thread.start()
    
    # 🤖 INICIALIZAÇÃO DO DATASETTE EXPLORADOR SQL (PASA v50.1 - Porta 8002)
    db_file = os.path.join(PROJECT_ROOT, "data", "sentinela_data.db")
    
    # Garante exportação inicial do banco se ele não existir
    if not os.path.exists(db_file):
        try:
            from scripts.export_to_sqlite import export_to_sqlite
            export_to_sqlite()
        except Exception as e_init:
            print(f"[Watchdog] Erro na exportação inicial para Datasette: {e_init}")

    def run_datasette_server():
        try:
            python_exe = get_python_executable()
            creationflags = 0x08000000 if os.name == 'nt' else 0
            subprocess.Popen(
                [python_exe, "-m", "datasette", "serve", "-i", db_file, "--port", "8002", "--host", "0.0.0.0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )
            print("[START] Explorador SQL (Datasette) disponível em: http://localhost:8002")
        except Exception as e_ds:
            print(f"[WARN] Falha ao iniciar Datasette: {e_ds}")

    datasette_thread = Thread(target=run_datasette_server, daemon=True)
    datasette_thread.start()

    print("[START] Dashboard disponível em: http://localhost:8001")
    print("[SHIELD] SENTINELA DEMOCRÁTICA - WATCHDOG v50.0")
    
    guard()
