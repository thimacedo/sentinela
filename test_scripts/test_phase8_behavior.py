import os
import sys
import asyncio
import logging

# --- AUTO-ANCHORING ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.behavior_engine import behavior_engine

logging.basicConfig(level=logging.INFO)

async def test_behavior_engine():
    print("🚀 Iniciando Teste de Detecção de Comportamento Coordenado (Fase 8)")
    
    comments = [
        {"id": 1, "texto_bruto": "Este candidato é o melhor para nossa cidade! Vamos votar 99!"},
        {"id": 2, "texto_bruto": "Este candidato é o melhor para nossa cidade! Vamos votar 99!"},
        {"id": 3, "texto_bruto": "Este candidato é o melhor para nossa cidade! Vamos votar 99!"},
        {"id": 4, "texto_bruto": "A proposta de educação é excelente. Parabéns."},
        {"id": 5, "texto_bruto": "Candidato nota 10, sempre com a verdade."},
        {"id": 6, "texto_bruto": "VAMOS VOTAR 99! O melhor para nossa cidade sempre."}, # Slogan similar
        {"id": 7, "texto_bruto": "VAMOS VOTAR 99! O melhor para nossa cidade sempre."},
        {"id": 8, "texto_bruto": "VAMOS VOTAR 99! O melhor para nossa cidade sempre."},
    ]
    
    print("\n--- Processando comentários ---")
    processed = behavior_engine.detect_coordinated_clusters(comments)
    
    bots = [c for c in processed if c.get("is_bot")]
    print(f"\n✅ Total de comentários processados: {len(processed)}")
    print(f"🤖 Comentários marcados como coordenados/bot: {len(bots)}")
    
    for b in bots:
        print(f"   ID {b['id']} | Padrão: {b['bot_pattern']} | Cluster: {b['cluster_id']} | Slogans: {b.get('slogans_detectados', [])}")

    # Teste de N-Gramas isolado
    print("\n--- Teste de Extração de N-Gramas ---")
    text = "A democracia é fundamental para o desenvolvimento do Brasil."
    bigrams = behavior_engine.extract_ngrams(text, 2)
    trigrams = behavior_engine.extract_ngrams(text, 3)
    print(f"Texto: {text}")
    print(f"Bigramas: {bigrams}")
    print(f"Trigramas: {trigrams}")

if __name__ == "__main__":
    asyncio.run(test_behavior_engine())
