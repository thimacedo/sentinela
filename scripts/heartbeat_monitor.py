"""
Sentinela Heartbeat Monitor (v98.2)
════════════════════════════════════════════════════════════════════
Monitor externo e independente do processo principal.
Registrado no Windows Task Scheduler — roda a cada 15 minutos
mesmo que o Watchdog ou o main_runner estejam travados/mortos.

Lógica:
  1. Lê MAX(data_coleta) diretamente do Supabase
  2. Se gap > HEARTBEAT_MAX_GAP_MIN (padrão: 90min):
     a. Verifica se o Watchdog responde em http://127.0.0.1:8001/api/status
     b. Registra system_event no Supabase
     c. Envia alerta WhatsApp
     d. Mata processos Python stale (Playwright incluso)
     e. Reinicia o Watchdog
  3. Loga cada verificação em logs/heartbeat.log

Uso manual:
  python scripts/heartbeat_monitor.py

Instalação automática (Task Scheduler):
  powershell -ExecutionPolicy Bypass -File scripts/setup_heartbeat_task.ps1
"""
import os
import sys
import time
import logging
import socket
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Bootstrap de ambiente ─────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Configuração ─────────────────────────────────────────────────
MAX_GAP_MIN      = int(os.getenv("HEARTBEAT_MAX_GAP_MIN", "15"))
WATCHDOG_URL     = os.getenv("WATCHDOG_URL", "http://127.0.0.1:8001")
WATCHDOG_TIMEOUT = int(os.getenv("WATCHDOG_TIMEOUT_S", "5"))
WHATSAPP_PHONE   = os.getenv("WHATSAPP_PHONE", "")
WHATSAPP_APIKEY  = os.getenv("WHATSAPP_API_KEY", "")
LOG_PATH         = ROOT / os.getenv("HEARTBEAT_LOG_PATH", "logs/heartbeat.log")
PYTHON_EXE       = sys.executable

# ── Logging ───────────────────────────────────────────────────────
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("heartbeat")


def _supabase_client():
    """Retorna cliente Supabase usando as mesmas variáveis do projeto."""
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SENTINELA_SUPABASE_KEY")
    return create_client(url, key)


def get_last_coleta_gap_min() -> float:
    """Retorna quantos minutos se passaram desde a última coleta no banco."""
    try:
        db = _supabase_client()
        result = db.table("comentarios") \
            .select("data_coleta") \
            .order("data_coleta", desc=True) \
            .limit(1) \
            .execute()

        if not result.data:
            log.warning("Tabela comentarios vazia ou inacessível.")
            return 9999.0

        ultima_str = result.data[0]["data_coleta"]
        ultima = datetime.fromisoformat(ultima_str.replace("Z", "+00:00"))
        gap = (datetime.now(timezone.utc) - ultima).total_seconds() / 60.0
        return gap

    except Exception as e:
        log.error("Erro ao consultar gap de coleta: %s", e)
        return 9999.0


def watchdog_is_alive() -> bool:
    """Testa se o Watchdog está ativo via socket na porta 8009 ou HTTP."""
    # Checagem primária via socket na porta 8009 (independe de lentidão do Uvicorn)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(("127.0.0.1", 8009))
        s.close()
        return True
    except Exception:
        pass

    try:
        urllib.request.urlopen(
            f"{WATCHDOG_URL}/api/status",
            timeout=WATCHDOG_TIMEOUT
        )
        return True
    except Exception:
        return False


def notify_whatsapp(message: str):
    """Envia alerta WhatsApp via CallMeBot."""
    if not WHATSAPP_PHONE or not WHATSAPP_APIKEY:
        return
    try:
        texto = f"🚨 [Sentinela Heartbeat] {message}"
        url = (
            f"https://api.callmebot.com/whatsapp.php"
            f"?phone={WHATSAPP_PHONE}&apikey={WHATSAPP_APIKEY}"
            f"&text={urllib.parse.quote(texto)}"
        )
        urllib.request.urlopen(url, timeout=8)
        log.info("Alerta WhatsApp enviado.")
    except Exception as e:
        log.warning("Falha ao enviar WhatsApp: %s", e)


def record_event_supabase(description: str, gap_min: float, action_taken: str):
    """Persiste o evento de heartbeat no Supabase para rastreabilidade."""
    try:
        db = _supabase_client()
        db.table("system_events").insert({
            "event_type": "COLETA_PARADA",
            "source": "heartbeat_monitor",
            "severity": "critical",
            "description": description,
            "metadata": {
                "gap_minutes": round(gap_min),
                "max_gap_min": MAX_GAP_MIN,
                "action_taken": action_taken,
                "hostname": socket.gethostname(),
                "trigger": "task_scheduler",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        log.info("Evento registrado no Supabase.")
    except Exception as e:
        log.warning("Falha ao registrar evento no Supabase: %s", e)


def kill_stale_processes():
    """
    Encerra processos Python stale relacionados ao Sentinela.
    Mata main_runner.py e processos Playwright/chromium que
    ficaram presos sem consumir fila.
    """
    try:
        # Windows: taskkill por nome do script
        result = subprocess.run(
            ["taskkill", "/F", "/FI", "IMAGENAME eq python.exe",
             "/FI", "WINDOWTITLE eq main_runner*"],
            capture_output=True, text=True, timeout=15
        )
        log.info("taskkill main_runner: %s", result.stdout.strip() or "sem processos encontrados")
    except Exception as e:
        log.warning("Erro ao matar processos stale: %s", e)

    # Aguarda 3s para os processos encerrarem
    time.sleep(3)


def restart_watchdog():
    """Reinicia o Watchdog em background (processo desanexado)."""
    watchdog_entry = ROOT / "watchdog" / "__init__.py"
    if not watchdog_entry.exists():
        # Tenta entrypoint alternativo
        watchdog_entry = ROOT / "run_watchdog.py"

    try:
        subprocess.Popen(
            [PYTHON_EXE, str(watchdog_entry)],
            cwd=str(ROOT),
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )
        log.info("Watchdog reiniciado em background: %s", watchdog_entry)
    except Exception as e:
        log.error("Falha ao reiniciar Watchdog: %s", e)


def run_check():
    """Executa uma verificação completa de saúde."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info("══ Verificação Heartbeat ══ %s", now)

    gap_min = get_last_coleta_gap_min()
    log.info("Gap de coleta: %.1f min (threshold: %d min)", gap_min, MAX_GAP_MIN)

    if gap_min <= MAX_GAP_MIN:
        log.info("✅ Sistema saudável. Nenhuma ação necessária.")
        return

    # ─── SISTEMA PARADO ───────────────────────────────────────────
    watchdog_alive = watchdog_is_alive()
    status_watchdog = "vivo" if watchdog_alive else "morto"

    descricao = (
        f"Coleta parada há {round(gap_min)} minutos "
        f"(threshold: {MAX_GAP_MIN}min). "
        f"Watchdog: {status_watchdog}. "
        f"Ação: reinício automático."
    )
    log.warning("⚠️  %s", descricao)

    # Notifica antes de agir
    notify_whatsapp(descricao)

    # Persiste no banco
    record_event_supabase(descricao, gap_min, action_taken="kill_stale + restart_watchdog")

    # Age: mata stale e reinicia
    if not watchdog_alive:
        log.warning("Watchdog não responde — reiniciando tudo.")
        kill_stale_processes()
        restart_watchdog()
    else:
        log.warning("Watchdog vivo mas coleta parada — reiniciando apenas main_runner via API.")
        try:
            urllib.request.urlopen(
                f"{WATCHDOG_URL}/api/server/restart",
                timeout=WATCHDOG_TIMEOUT
            )
            log.info("Restart enviado via API do Watchdog.")
        except Exception as e:
            log.warning("API do Watchdog falhou (%s). Reiniciando manualmente.", e)
            kill_stale_processes()
            restart_watchdog()

    log.info("Ação concluída. Próxima verificação em 15 minutos.")


if __name__ == "__main__":
    run_check()
