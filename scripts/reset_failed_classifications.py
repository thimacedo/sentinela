import asyncio
import os
import sys

# Garante importação correta dos módulos do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(override=True)

async def main():
    try:
        from core.db import db_client
        print("Saneamento de Banco de Dados - Sentinela")
        print("Buscando comentários marcados com categoria 'ERRO'...")
        
        # Primeiro, pegamos a contagem para confirmar
        count_res = db_client.client.table('comentarios').select('id', count='exact').eq('categoria_ia', 'ERRO').execute()
        total_affected = count_res.count or 0
        print(f"Total de registros a serem redefinidos: {total_affected}")
        
        if total_affected == 0:
            print("Nenhum registro com erro para limpar.")
            return

        print("Iniciando redefinição...")
        # Tenta atualizar de uma vez usando o filtro do Postgrest
        try:
            update_res = db_client.client.table('comentarios')\
                .update({
                    "processado_ia": False,
                    "categoria_ia": None,
                    "confianca_ia": None,
                    "is_hate": None,
                    "analise_pericial": None
                })\
                .eq('categoria_ia', 'ERRO')\
                .execute()
            print(f"[OK] Saneamento concluído! Registros redefinidos com sucesso.")
        except Exception as e_batch:
            print(f"Falha ao redefinir todos de uma vez: {e_batch}. Tentando processamento por lote de IDs...")
            # Fallback: seleciona os IDs e atualiza em lotes de 100
            ids_res = db_client.client.table('comentarios').select('id').eq('categoria_ia', 'ERRO').limit(1000).execute()
            ids = [item["id"] for item in (ids_res.data or [])]
            
            chunk_size = 100
            for i in range(0, len(ids), chunk_size):
                chunk = ids[i:i+chunk_size]
                db_client.client.table('comentarios').update({
                    "processado_ia": False,
                    "categoria_ia": None,
                    "confianca_ia": None,
                    "is_hate": None,
                    "analise_pericial": None
                }).in_('id', chunk).execute()
                print(f"Lote de {len(chunk)} registros atualizado...")
            
    except Exception as e:
        print(f"❌ Erro crítico no script de saneamento: {e}")

if __name__ == "__main__":
    asyncio.run(main())
