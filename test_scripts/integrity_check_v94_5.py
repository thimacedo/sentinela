import asyncio
import os
import sys
import logging

# --- AUTO-ANCHORING ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.ai_service import ai_service
from core.circuit_breaker import ai_circuit_breaker, scraper_circuit_breaker
from core.behavior_engine import behavior_engine
from core.lexical_filter import lexical_filter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrityCheck")

async def run_integrity_check():
    logger.info("🛡️ Iniciando Verificação de Integridade Sentinela v94.5")
    
    # 1. Teste de IA Mesh (Mock)
    logger.info("Testing IA Mesh logic...")
    # Verifica se o método de reanálise existe (sem executar chamada cloud real para poupar tokens)
    assert hasattr(ai_service, 'run_batch_reanalysis'), "ai_service.run_batch_reanalysis missing"
    
    # 2. Teste de Circuit Breaker v2
    logger.info("Testing Circuit Breaker v2 states...")
    scraper_circuit_breaker.record_failure("test_service", status_code=429)
    status = scraper_circuit_breaker._get_status("test_service")
    assert status.state == "OPEN", "Circuit Breaker failed to OPEN on 429"
    logger.info(f"   CB Status: {status.state} (Open until {status.open_until})")
    
    # 3. Teste de Behavior Engine (N-Gramas)
    logger.info("Testing Behavior Engine (N-Grams)...")
    text = "Isso é um teste de slogan repetitivo. Isso é um teste de slogan repetitivo."
    ngrams = behavior_engine.extract_ngrams(text, 3)
    assert len(ngrams) > 0, "Behavior Engine failed to extract trigrams"
    logger.info(f"   Sample N-Gram: {ngrams[0]}")
    
    # 4. Teste de Shadowban Léxico
    logger.info("Testing Shadowban Lexical...")
    spam_text = "Ganhe dinheiro fácil no cassino link na bio bet99"
    assert lexical_filter.should_shadowban(spam_text) == True, "Shadowban failed to detect spam"
    logger.info("   Shadowban detected spam correctly.")

    logger.info("✅ Todos os subsistemas principais passaram na verificação de integridade técnica.")

if __name__ == "__main__":
    asyncio.run(run_integrity_check())
