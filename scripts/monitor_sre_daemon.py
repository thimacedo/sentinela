# Daemon de Monitoramento Ativo e Autocura SRE (v1.0)
# Arquivo: scripts/monitor_sre_daemon.py

import os
import sys
import time
import json
import psutil
import subprocess
import logging
from datetime import datetime, timezone
from pathlib import Path

# Configura encoding UTF-8 no Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

BASE_PATH = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_PATH / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuração de logs específicos do daemon de monitoramento
log_file = LOG_DIR / "monitoramento_sre.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sre.monitor")

AGENT_SCRIPT = BASE_PATH / "sentinela_autonomous_agent.py"
AGENT_STATUS = BASE_PATH / "agent.status.json"
HEALTH_CHECK_SCRIPT = BASE_PATH / "scripts" / "cj_sre_health_check.py"
VENV_PYTHON = BASE_PATH / ".venv" / "Scripts" / "python.exe"

if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable) # Fallback para python ativo

def is_agent_running():
    """Verifica se o processo do agente autonomo esta ativo."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline'] or []
            cmd_str = " ".join(cmdline).lower()
            if "python" in proc.info['name'].lower() and "sentinela_autonomous_agent.py" in cmd_str:
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def restart_agent():
    """Inicia uma nova instancia do agente autonomo em background."""
    logger.warning("🚨 [SRE] Reiniciando agente autonomo...")
    try:
        # Executa em background de forma independente
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BASE_PATH)
        subprocess.Popen(
            [str(VENV_PYTHON), str(AGENT_SCRIPT)],
            cwd=str(BASE_PATH),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith("win") else 0
        )
        logger.info("✅ [SRE] Nova instancia do agente autonomo disparada com sucesso.")
    except Exception as e:
        logger.error(f"❌ [SRE] Erro ao disparar agente: {e}")

def run_health_check():
    """Executa o script de destravamento de locks."""
    logger.info("🔄 [SRE] Disparando cj_sre_health_check para destravamento de fila...")
    try:
        subprocess.run(
            [str(VENV_PYTHON), str(HEALTH_CHECK_SCRIPT)],
            cwd=str(BASE_PATH),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        logger.error(f"❌ [SRE] Erro ao rodar health check: {e}")

def monitor_cycle():
    # 1. Verifica processo do agente
    pid = is_agent_running()
    if not pid:
        logger.error("🚨 [SRE] Agente nao esta rodando! Iniciando autocura...")
        restart_agent()
        return False
        
    # 2. Verifica batimento do agent.status.json
    if not AGENT_STATUS.exists():
        logger.warning("⚠️ [SRE] Arquivo agent.status.json nao encontrado.")
        return False

    try:
        with open(AGENT_STATUS, "r", encoding="utf-8") as f:
            status = json.load(f)
            
        hb_str = status.get("last_heartbeat")
        state = status.get("status", "UNKNOWN")
        consecutive_blocks = status.get("consecutive_blocks", 0)
        
        # Verifica timeout do Heartbeat (lag > 120s indica congelamento, tolerância de 400s no Modo Noturno)
        if hb_str:
            # Exemplo: 2026-07-04T07:02:52.728732+00:00 ou similar
            hb_clean = hb_str.split(".")[0].replace("Z", "")
            if "+" in hb_clean:
                hb_clean = hb_clean.split("+")[0]
            if "T" in hb_clean:
                hb_dt = datetime.strptime(hb_clean, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            else:
                hb_dt = datetime.strptime(hb_clean, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                
            lag = (datetime.now(timezone.utc) - hb_dt).total_seconds()
            
            # Ajusta threshold de lag dinamicamente conforme horário (margens seguras para evitar falsos positivos de latência ou sleeps)
            current_hour = datetime.now().hour
            is_night = current_hour >= 23 or current_hour < 6
            max_lag = 900 if is_night else 600
            
            if lag > max_lag:
                logger.error(f"🚨 [SRE] Agente congelado! Heartbeat inativo ha {lag:.1f}s. Forcando reinicializacao...")
                # Mata processo zumbi e reinicia
                try:
                    p = psutil.Process(pid)
                    p.kill()
                    logger.info(f"💀 [SRE] Processo zumbi PID {pid} encerrado.")
                except Exception as e_kill:
                    logger.error(f"❌ [SRE] Erro ao matar zumbi PID {pid}: {e_kill}")
                restart_agent()
                return False
                
        # 3. Verifica se o status do agente esta travado ou pausado
        if state == "CRITICAL" or consecutive_blocks >= 3:
            logger.error(f"🚨 [SRE] Agente em estado critico: {state} | Bloqueios: {consecutive_blocks}. Acionando reparo...")
            run_health_check()
            
        logger.info(f"💚 [SRE] Agente ativo (PID: {pid}) | Status: {state} | Heartbeat Lag: {lag:.1f}s | Fila Pendente: {status.get('pending_queue', 0)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ [SRE] Erro na leitura de telemetria: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO DAEMON DE MONITORAMENTO ATIVO SRE — SENTINELA")
    logger.info("=" * 60)
    logger.info(f"Intervalo: 15s | Duracao: 1 hora (3600s)")
    
    start_time = time.time()
    duration = 3600 # 1 hora
    interval = 15 # 15 segundos
    
    cycle = 0
    while time.time() - start_time < duration:
        cycle += 1
        monitor_cycle()
        time.sleep(interval)
        
    logger.info("=" * 60)
    logger.info("DAEMON DE MONITORAMENTO SRE CONCLUÍDO COM SUCESSO (1 HORA)")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
