import os
import sys
import asyncio

# --- AUTO-ANCHORING (v61.6) ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.pasa_auditor import PASAAuditor

# Teste de pipeline analitico
async def main():
    auditor = PASAAuditor()
    result = await auditor.process("O perito encontrou uma prova forense.")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
