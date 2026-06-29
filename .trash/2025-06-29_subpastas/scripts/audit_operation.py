import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, UTC, timedelta
from dotenv import load_dotenv

# Garante o PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env", override=True)

from core.db import db_client

async def audit():
    print(f"🕵️ Auditoria Operacional Sentinela - {datetime.now(UTC).isoformat()}")
    print("-" * 50)
    
    try:
        # 1. Alertas Críticos (Últimas 12h)
        since = (datetime.now(UTC) - timedelta(hours=12)).isoformat()
        res_alerts = await asyncio.to_thread(
            db_client.client.table('system_alerts')
            .select('*')
            .gte('created_at', since)
            .order('created_at', desc=True)
            .execute
        )
        alerts = res_alerts.data or []
        print(f"🚨 Alertas Críticos (12h): {len(alerts)}")
        for a in alerts[:5]:
            print(f"  [{a['severidade']}] {a['titulo']}: {a['descricao'][:100]}...")

        # 2. Métricas de Workers (Últimos ciclos)
        res_metrics = await asyncio.to_thread(
            db_client.client.table('worker_metrics')
            .select('worker_id, items_failed, items_collected, timestamp, errors')
            .order('timestamp', desc=True)
            .limit(20)
            .execute
        )
        metrics = res_metrics.data or []
        print(f"\n📊 Últimos 20 Ciclos de Workers:")
        fail_count = 0
        for m in metrics:
            is_fail = (m.get('items_failed') or 0) > 0 or m.get('errors')
            status = "❌ FAIL" if is_fail else "✅ OK"
            if is_fail: fail_count += 1
            err_msg = str(m.get('errors') or '-')[:50]
            print(f"  {m['timestamp'][11:19]} | {m['worker_id']:<20} | {status} | {err_msg}")
        
        print(f"\n📈 Taxa de Erro na amostra: {(fail_count/20)*100:.1f}%")

        # 3. Sugestões de IA (Pendentes)
        res_sug = await asyncio.to_thread(
            db_client.client.table('worker_suggestions')
            .select('*')
            .eq('status', 'pending_review')
            .execute
        )
        suggs = res_sug.data or []
        print(f"\n💡 Sugestões de Autocura Pendentes: {len(suggs)}")
        for s in suggs[:3]:
            print(f"  - {s['worker_id']}: {s['suggestion'][:80]}...")

    except Exception as e:
        print(f"❌ Erro na auditoria: {e}")

if __name__ == "__main__":
    asyncio.run(audit())
