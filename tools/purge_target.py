import os
import sys
from dotenv import load_dotenv

# Garante que o diretório raiz do projeto esteja no path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.supabase_service import supabase
    print("✅ Conexão com Supabase estabelecida.")
except ImportError:
    print("❌ Erro: Não foi possível importar o serviço do Supabase. Verifique o PYTHONPATH.")
    sys.exit(1)

def purge_target(username: str):
    """
    Desativa um alvo na tabela principal 'candidatos' e o remove da fila de coleta 'fila_coleta'.
    """
    if not username:
        print("❌ Username não fornecido.")
        return

    try:
        # --- Etapa 1: Desativar na tabela de candidatos ---
        print(f"🔄 Etapa 1: Tentando desativar @{username} na tabela 'candidatos'...")
        update_response = supabase.table('candidatos').update({
            'status_monitoramento': 'Inativo'
        }).eq('username', username).execute()
        
        update_count = update_response.count
        if update_count is not None and update_count > 0:
            print(f"✅ Sucesso: {update_count} registro(s) para @{username} marcados como 'Inativo'.")
        else:
            print(f"ℹ️ Info: @{username} não foi encontrado na tabela 'candidatos' para desativação.")

        # --- Etapa 2: Remover da fila de coleta pendente ---
        print(f"🔄 Etapa 2: Tentando remover @{username} da 'fila_coleta'...")
        delete_response = supabase.table('fila_coleta').delete().eq('candidato_id', username).execute()
        
        delete_count = delete_response.count
        if delete_count is not None and delete_count > 0:
            print(f"✅ Sucesso: {delete_count} entrada(s) para @{username} removidas da fila de coleta.")
        else:
            print(f"ℹ️ Info: @{username} não encontrado na 'fila_coleta' pendente.")

    except Exception as e:
        print(f"❌ Erro crítico durante a operação no banco de dados: {e}")

if __name__ == "__main__":
    target_to_purge = sys.argv[1] if len(sys.argv) > 1 else "claudiocastrooficial"
    purge_target(target_to_purge)
