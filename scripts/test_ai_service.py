import asyncio
import logging
import os
import sys

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(override=True)

from core.ai_service import AIService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

async def test_ai_routing():
    print("[*] Iniciando teste de roteamento de IA...")
    ai = AIService()
    
    # Lista provedores configurados
    providers = [p["name"] for p in ai.providers]
    print(f"[*] Provedores ativos: {providers}")
    
    test_text = "Esse político é um lixo, devia ser expulso do país!"
    print(f"[*] Testando classificação de: \"{test_text}\"")
    
    try:
        result = await ai.classify_text(test_text)
        print("\n[OK] Resultado da Classificação:")
        print(f"  - Categoria: {result.get('categoria_ia')}")
        print(f"  - Is Hate: {result.get('is_hate')}")
        print(f"  - Confiança: {result.get('confianca_ia')}")
        print(f"  - Análise: {result.get('analise_pericial')}")
    except Exception as e:
        print(f"\n[ERROR] Falha na classificação: {e}")

if __name__ == "__main__":
    # Garante que ENABLE_LOCAL_AI esteja ligado para o teste se o usuário quiser testar Ollama
    if os.getenv("ENABLE_LOCAL_AI") == "true":
        print("[!] TESTE COM OLLAMA ATIVO")
    
    asyncio.run(test_ai_routing())
