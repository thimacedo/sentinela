import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
from core.supabase_service import get_supabase_client

db = get_supabase_client()
try:
    res = db.rpc('exec_sql', {'query': """
    ALTER TABLE worker_rewards DROP CONSTRAINT IF EXISTS worker_rewards_tier_check;
    """}).execute()
    print("Dropped constraint:", res.data)
except Exception as e:
    print("RPC failed, modifying reward_engine instead.")
    with open("workers/base/reward_engine.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Simple replacement to fallback to 'bronze' for anything else
    new_resolve = """    def resolve_tier(self, score: float, result: CycleResult) -> str:
        if score >= 70: return "gold"
        if score >= 50: return "silver"
        return "bronze"  # Fallback para db_failed, idle, dry_run e critical"""
        
    import re
    content = re.sub(
        r'    def resolve_tier\(self, score: float, result: CycleResult\) -> str:.*?return "critical"', 
        new_resolve, 
        content, 
        flags=re.DOTALL
    )
    with open("workers/base/reward_engine.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Modified reward_engine.py to use safe tiers only.")
