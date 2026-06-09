import asyncio
import sys
import os
import json

# --- AUTO-ANCHORING ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from core.intelligence_service import intelligence_service

async def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/add_target.py <username_instagram>")
        return

    username = sys.argv[1]
    print(f"🚀 Iniciando processo de inclusão inteligente para @{username}...")
    
    result = await intelligence_service.research_and_validate(username)
    
    if result:
        print("\n✅ Inclusão Concluída!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Falha ao processar o alvo @{username}. Verifique os logs.")

if __name__ == "__main__":
    asyncio.run(main())
