
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import os
from dotenv import load_dotenv
# Remove direct Supabase client imports and usage
# from supabase import create_client, Client 

# Import the new SupabaseService and the global instance
from core.supabase_service import SupabaseService, supabase_client_instance
from core.config import settings

# The previous global Supabase client setup is now handled within core.supabase_service.py
# We will use the imported supabase_client_instance

async def fetch_and_process_pending():
    """
    Busca comentários pendentes de análise, processa-os (placeholder)
    e atualiza seu status no Supabase.
    Utiliza o SupabaseService para interações com o banco de dados.
    """
    if not supabase_client_instance:
        print("❌ Erro: Cliente Supabase não inicializado. Não é possível prosseguir.")
        return

    print("Buscando lote de comentários pendentes...")
    try:
        # Utiliza o método do novo serviço para buscar comentários
        registros = await supabase_client_instance.fetch_unprocessed_comments(limit=100)
        
        if not registros:
            print("Nenhum comentário pendente de análise encontrado.")
            return

        print(f"Encontrados {len(registros)} registros pendentes. Iniciando processamento...")

        processados_com_sucesso = 0
        erros_atualizacao = 0
        ignorados_vazios = 0

        for row in registros:
            comment_id = row.get('id')
            if not comment_id:
                print(f"⚠️ Aviso: Registro sem ID encontrado, ignorando: {row}")
                erros_atualizacao += 1
                continue

            # Fallback seguro: se texto_limpo for null ou vazio, usa texto_bruto
            texto_analise = row.get('texto_limpo')
            if not texto_analise or str(texto_analise).strip() == "":
                texto_analise = row.get('texto_bruto')

            if texto_analise and str(texto_analise).strip() != "":
                try:
                    # TODO: Inserir aqui a chamada para a API de IA no futuro
                    # Por enquanto, apenas marca como processado.
                    
                    # Marca como processado no banco usando o novo serviço
                    await supabase_client_instance.update_comment_classification(
                        comment_id=str(comment_id), # Garantir que o ID é string se necessário
                        data={'processado_ia': True}
                    )
                    
                    processados_com_sucesso += 1
                except Exception as db_err:
                    print(f"❌ Erro ao atualizar ID {comment_id} no Supabase: {db_err}")
                    erros_atualizacao += 1
            else:
                # Se cair aqui, é porque texto_limpo e texto_bruto estão vazios/null
                ignorados_vazios += 1

        print("\n--- Resumo do Processamento ---")
        print(f"Lote total analisado: {len(registros)} comentários")
        print(f"Atualizados com sucesso: {processados_com_sucesso}")
        print(f"Ignorados (sem texto): {ignorados_vazios}")
        print(f"Falhas na atualização: {erros_atualizacao}")
        print("-------------------------------")

    except Exception as e:
        # Captura erros gerais durante a busca ou lógica inicial
        print(f"❌ Erro fatal na execução do fetch_and_process_pending: {str(e)}")

if __name__ == "__main__":
    # Para executar este script diretamente, precisamos de um loop de eventos asyncio
    # Se for executado como script principal, `asyncio.run` é necessário.
    import asyncio
    asyncio.run(fetch_and_process_pending())
