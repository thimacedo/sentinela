# scratch/test_ai_cleanup.py
import asyncio
import sys
import os

# Adiciona o diretório raiz ao path para conseguir importar o core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.ai_service import clean_null_chars, ai_service

async def main():
    print("=== Testando higienização de caracteres nulos ===")
    test_data = {
        "categoria_ia": "VIOLÊNCIA_GÊNERO\u0000",
        "evidencia_lexical": ["vagabunda\u0000", "lixo\x00"],
        "analise_pericial": "O comentário contém xingamentos direcionados.\u0000"
    }
    
    cleaned = clean_null_chars(test_data)
    print("Dado original:", repr(test_data))
    print("Dado limpo:   ", repr(cleaned))
    
    # Verifica se os caracteres nulos sumiram
    assert "\u0000" not in cleaned["categoria_ia"]
    assert "\u0000" not in cleaned["evidencia_lexical"][0]
    assert "\x00" not in cleaned["evidencia_lexical"][1]
    assert "\u0000" not in cleaned["analise_pericial"]
    print("[OK] Sucesso na higienizacao de caracteres nulos!")
    
    print("\n=== Testando Classificação de Texto Assíncrona ===")
    test_comment = "Você é um idiota completo do Sul que só sabe falar besteira e odeia nordestinos!"
    print(f"Comentário de teste: '{test_comment}'")
    
    try:
        # Testa a classificação real (vai usar Mistral -> Groq -> OpenRouter)
        result = await ai_service.classify_text(test_comment)
        print("Resultado da classificação:")
        for k, v in result.items():
            print(f"  {k}: {repr(v)}")
        print("[OK] Sucesso no teste de classificacao de IA!")
    except Exception as e:
        print(f"[ERRO] Falha no teste de classificacao: {e}")

if __name__ == "__main__":
    asyncio.run(main())
