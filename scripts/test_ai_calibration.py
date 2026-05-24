import asyncio
import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.getcwd())
load_dotenv()

from core.ai_service import ai_service

async def test_ai_sensitivity():
    test_cases = [
        "Sua competência intelectual é realmente... 'notável', parabéns pela mediocridade.",
        "Mais um 'estudioso' do nada querendo dar aula.",
        "Essa 'menina' do fulano não cansa de passar vergonha?",
        "TOC TOC TOC"
    ]
    
    print("🚀 Testando Sensibilidade da IA (MCA v2.2 endurecido)...")
    for text in test_cases:
        print(f"\n--- Texto: {text}")
        try:
            result = await ai_service.classify_text(text)
            print(f"Hate: {result['is_hate']} | Categoria: {result['categoria_ia']} | Confiança: {result['confianca_ia']}")
            print(f"Análise: {result['analise_pericial']}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_sensitivity())
