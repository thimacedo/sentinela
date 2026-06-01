import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import logging
from pathlib import Path
from core.fallback_llm import FallbackLLM
from core.supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename=Path(__file__).with_suffix('.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

INTERVAL_SECONDS = int(os.getenv('WATCHDOG_INTERVAL', '300'))  # default 5 min

def health_check():
    try:
        llm = FallbackLLM()
        response = llm.classify("Teste de saúde do fallback.")
        logging.info('Health check OK: %s', response[:100])
        # Log to Supabase
        supabase = get_supabase_client()
        supabase.table('fallback_logs').insert({
            'provider': 'watchdog',
            'status': 'OK',
            'payload': {'response': response}
        }).execute()
    except Exception as e:
        logging.error('Health check FAILED: %s', e)
        supabase = get_supabase_client()
        supabase.table('fallback_logs').insert({
            'provider': 'watchdog',
            'status': 'FAIL',
            'payload': {'error': str(e)}
        }).execute()

if __name__ == '__main__':
    logging.info('Iniciando watchdog de fallback')
    while True:
        health_check()
        time.sleep(INTERVAL_SECONDS)
