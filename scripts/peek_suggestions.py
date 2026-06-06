import sys
import os
from pathlib import Path

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db import db_client
import json

def get_recent_suggestions():
    res = db_client.client.table('worker_suggestions').select('*').eq('status', 'pending_review').order('timestamp', desc=True).limit(5).execute()
    for s in res.data:
        print(f"[{s['worker_id']}] {s['suggestion']}\n")
        print("-" * 30)

if __name__ == "__main__":
    get_recent_suggestions()
