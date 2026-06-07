import asyncio
import os
import sys
import yaml
from datetime import datetime

# Ensure the project root is in PYTHONPATH
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(override=True)

from core.ai_service import AIService

# Sample texts covering different categories
SAMPLE_TEXTS = [
    "Esse político é um lixo, devia ser expulso do país!",  # Expected INSULTO_AD_HOMINEM
    "Eu apoio a igualdade de gênero e a proteção dos direitos humanos.",  # Expected NEUTRO
    "Aquele grupo está tentando destruir nossa cultura e precisamos lutar contra eles.",  # Expected ODIO_IDENTITARIO
]

# Load fallback providers configuration
CONFIG_PATH = os.path.join(os.getcwd(), "config", "fallback_providers.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    fallback_cfg = yaml.safe_load(f)

# Helper to build a temporary AIService with a single provider
def build_service_for(provider_name: str, provider_cfg: dict) -> AIService:
    service = AIService()
    # Preserve original providers order
    original = service.providers.copy()
    # Find matching provider in original list
    matched = next((p for p in original if p["name"] == provider_name), None)
    if not matched:
        # If not found (e.g., abacus), create a dummy client that raises NotImplementedError
        # This will trigger the fallback mechanism, which is fine for testing.
        matched = {"name": provider_name, "client": None, "model": "dummy", "timeout": 10.0}
    # Replace the providers list with only the chosen one
    service.providers = [matched]
    return service

async def test_fallbacks():
    print("[*] Iniciando teste de fallback individual...")
    for name, cfg in fallback_cfg.get("fallback_providers", {}).items():
        print(f"\n=== Provider: {name.upper()} ===")
        # Build service limited to this provider
        ai = build_service_for(name, cfg)
        for txt in SAMPLE_TEXTS:
            try:
                result = await ai.classify_text(txt, comment_id="test")
                print(f"[Texto] {txt[:30]}... -> categoria: {result.get('categoria_ia')}, is_hate: {result.get('is_hate')}, confiança: {result.get('confianca_ia'):.2f}")
            except Exception as e:
                print(f"[ERRO] Falha ao classificar com {name}: {e}")
            # Respectful delay to avoid rate‑limit 429 (5 s)
            await asyncio.sleep(5)
        # Small pause before next provider
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_fallbacks())
