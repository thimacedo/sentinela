import os
import time
import requests
import subprocess
import logging
from datetime import datetime, timedelta

# Configuração de Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] YOLO_SENTINEL: %(message)s',
    handlers=[
        logging.FileHandler("logs/yolo_sentinel.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("YOLO_SENTINEL")

WATCHDOG_URL = "http://localhost:8001/api/metrics"
DURATION_HOURS = 7
CHECK_INTERVAL_SECONDS = 1800  # 30 minutos

def start_watchdog():
    logger.info("🚀 Iniciando Watchdog em background...")
    # Usa 'python -m watchdog' assumindo que o diretório atual é a raiz e watchdog é um pacote
    # Ou 'python watchdog/__main__.py'
    process = subprocess.Popen(
        [sys.executable, "-m", "watchdog"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    return process

import sys

def check_status():
    try:
        response = requests.get(WATCHDOG_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao Watchdog: {e}")
    return None

def main():
    end_time = datetime.now() + timedelta(hours=DURATION_HOURS)
    logger.info(f"🛡️ Sentinela YOLO ativado. Fim previsto: {end_time.strftime('%H:%M:%S')}")
    
    # Verifica se watchdog já está rodando
    status = check_status()
    if not status:
        start_watchdog()
        time.sleep(10) # Espera inicializar
    
    while datetime.now() < end_time:
        status = check_status()
        if status:
            current_status = status.get("status", "DESCONHECIDO")
            restarts = status.get("restarts", 0)
            code_errors = status.get("code_errors", 0)
            
            logger.info(f"📊 Status: {current_status} | Restarts: {restarts} | Erros de Código: {code_errors}")
            
            if "PARADO" in current_status or code_errors >= 3:
                logger.error("🚨 Watchdog parado ou com muitos erros de código! Tentando reinicialização forçada...")
                # Aqui um humano/IA deveria intervir. Como script, tentamos limpar e reiniciar.
                start_watchdog()
        else:
            logger.warning("⚠️ Watchdog não responde. Tentando reiniciar...")
            start_watchdog()
            
        # Espera 30 minutos
        time.sleep(CHECK_INTERVAL_SECONDS)

    logger.info("🏁 Período de 7 horas concluído. Encerrando Sentinela.")

if __name__ == "__main__":
    main()
