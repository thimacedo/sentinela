import asyncio
import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import db_client
from core.ai_service import ai_service

async def main():
    comment_id = '4380a906-ff56-4cae-895d-4f0c9e72822f'
    
    # 1. Busca o texto original no banco
    res = db_client.client.table('comentarios').select('texto_bruto').eq('id', comment_id).execute()
    if not res.data:
        print("Comentário não encontrado no banco de dados.")
        return
        
    texto_bruto = res.data[0]['texto_bruto']
    print(f"Texto original encontrado ({len(texto_bruto)} caracteres).")
    
    # 2. Força a classificação utilizando os modelos Cloud de alta fidelidade
    # Removendo o Ollama da lista de providers temporariamente
    original_providers = list(ai_service.providers)
    ai_service.providers = [p for p in original_providers if p["name"] not in ["ollama"]]
    
    try:
        print("Iniciando classificação pericial (Cloud)...")
        res_ia = await ai_service.classify_text(texto_bruto, comment_id)
        
        print("\n--- Resultado da IA ---")
        print(f"Categoria: {res_ia.get('categoria_ia')}")
        print(f"É Ódio: {res_ia.get('is_hate')}")
        print(f"Confiança: {res_ia.get('confianca_ia')}")
        print(f"Perícia: {res_ia.get('analise_pericial')}")
        print("-----------------------\n")
        
        # 3. Atualiza o banco de dados
        if res_ia and "categoria_ia" in res_ia:
            update_data = {
                "categoria_ia": res_ia["categoria_ia"],
                "is_hate": res_ia["is_hate"],
                "confianca_ia": res_ia["confianca_ia"],
                "analise_pericial": res_ia.get("analise_pericial", "Revisão forçada via script de auditoria."),
                "processado_ia": True
            }
            update_res = db_client.client.table('comentarios').update(update_data).eq('id', comment_id).execute()
            print("✅ Banco de dados atualizado com sucesso.")
        else:
            print("❌ Falha ao obter classificação válida.")
            
    finally:
        # Restaura os provedores
        ai_service.providers = original_providers

if __name__ == "__main__":
    asyncio.run(main())