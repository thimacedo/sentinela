import sys
import os
from pathlib import Path

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import db_client

def check_sessions():
    print("🕵️ Verificando saúde das Sessões Instagram...")
    res = db_client.client.table('worker_sessions').select('*').execute()
    for s in res.data:
        status = s.get('status', 'N/A')
        fail_count = s.get('consecutive_failures', 0)
        user = s.get('username', 'N/A')
        last_err = s.get('last_error', '-')
        print(f"  [{s['id']}] {user:<15} | Status: {status:<10} | Falhas: {fail_count:<3} | Último Erro: {last_err[:50]}")

if __name__ == "__main__":
    check_sessions()
