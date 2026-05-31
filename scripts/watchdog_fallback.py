import os
import time
import logging
from pathlib import Path
from core.fallback_llm import FallbackLLM
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename=Path(__file__).with_suffix('.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

INTERVAL_SECONDS = int(os.getenv('WATCHDOG_INTERVAL', '300'))  # 5 minutes by default

def health_check():
    try:
        llm = FallbackLLM()
        # texto simples para teste de saúde
        response = llm.classify("Teste de saúde do fallback.")
        logging.info('Health check OK: %s', response[:100])
    except Exception as e:
        logging.error('Health check FAILED: %s', e)
        # Here you could add notification logic (e.g., webhook, email)

if __name__ == '__main__':
    logging.info('Iniciando watchdog de fallback')
    while True:
        health_check()
        time.sleep(INTERVAL_SECONDS)
