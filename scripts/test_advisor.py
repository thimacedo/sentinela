import asyncio
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env", override=True)

from workers.base.memory_store import MemoryStore
from workers.base.cycle_result import CycleResult
from workers.ai.doc_fetcher import DocFetcher
from workers.ai.sa_diagnostica_sistemas import SaDiagnosticaSistemas

logging.basicConfig(level=logging.INFO)

async def test_advisor():
    print("🚀 Testando SaDiagnosticaSistemas...")
    
    store = MemoryStore()
    fetcher = DocFetcher()
    advisor = SaDiagnosticaSistemas(store, fetcher)
    
    # Simula um resultado degradado
    fake_result = CycleResult(
        worker_id="ig-v2-01",
        cycle=999,
        target="@alvo_teste",
        source="SCRAPER_V2",
        extracted=0,
        inserted=0,
        failed=10,
        error="429 Too Many Requests - Session Blocked",
        db_success=True,
        metadata={"duration_seconds": 45.5}
    )
    
    # Criamos um objeto "worker" fake que o orquestrador passaria
    class FakeWorker:
        def __init__(self):
            self.worker_id = "ig-v2-01"
            
    worker = FakeWorker()
    
    print("🤖 Chamando analyze_and_suggest...")
    await advisor.analyze_and_suggest(worker, fake_result)
    
    print("✅ Teste finalizado. Verifique os logs e o Supabase.")

if __name__ == "__main__":
    asyncio.run(test_advisor())
