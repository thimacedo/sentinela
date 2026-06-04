import asyncio
import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(override=True)

from core.ai_service import AIService

async def supervised_test():
    print("[*] Iniciando teste supervisionado de IA...")
    ai = AIService()
    print(f"[*] Provedores configurados: {[p['name'] for p in ai.providers]}")
    test_text = "Este comentário contém discurso de ódio e deve ser classificado como insulto."
    print(f"[*] Texto de teste: \"{test_text}\"")
    try:
        result = await ai.classify_text(test_text)
        print("\n[OK] Resultado da classificação:")
        for k, v in result.items():
            print(f"  - {k}: {v}")
    except Exception as e:
        print(f"[ERROR] Falha na classificação: {e}")

if __name__ == "__main__":
    asyncio.run(supervised_test())
