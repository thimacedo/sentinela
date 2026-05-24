import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    oficial_username = 'guilhermeboulos.oficial'
    oficial_id = '141b5779-7a0d-41c5-867b-4b32810a48ea'
    
    duplicados = [
        {'id': '3d37a36d-1219-4e33-baf1-327a6f05b58a', 'username': 'guilherme_boulos'},
        {'id': '8ced2007-eed0-4dd3-8712-22742eb3c3a1', 'username': 'boulos_oficial'},
        {'id': '066a6429-9fad-4010-8688-e9b4418a8ec7', 'username': 'guilhermeboulos_sp'}
    ]
    
    print("[*] Iniciando higienização cadastral do alvo Guilherme Boulos...")
    
    # 1. Atualizar registro oficial
    try:
        print(f"[*] Atualizando registro oficial ({oficial_username}) com cargo e status ativo...")
        res = supabase.table('candidatos').update({
            'cargo': 'Deputado Federal',
            'status_monitoramento': 'Ativo',
            'prioridade_coleta': 10
        }).eq('id', oficial_id).execute()
        print(f"[OK] Registro oficial atualizado com sucesso. Retorno: {res.data}")
    except Exception as e:
        print(f"💥 Erro ao atualizar registro oficial: {e}")
        return
        
    # 2. Inativar registros duplicados
    for dup in duplicados:
        try:
            print(f"[*] Inativando duplicado: @{dup['username']} (ID: {dup['id']})...")
            res = supabase.table('candidatos').update({
                'status_monitoramento': 'Inativo'
            }).eq('id', dup['id']).execute()
            print(f"[OK] Duplicado @{dup['username']} inativado.")
        except Exception as e:
            print(f"💥 Erro ao inativar duplicado @{dup['username']}: {e}")
            
    # 3. Limpar a fila de coleta para os duplicados inativados
    for dup in duplicados:
        try:
            print(f"[*] Removendo @{dup['username']} da fila de coleta (fila_coleta)...")
            # Remove usando candidato_id igual ao username
            res1 = supabase.table('fila_coleta').delete().eq('candidato_id', dup['username']).execute()
            # Remove usando candidato_id igual ao UUID
            res2 = supabase.table('fila_coleta').delete().eq('candidato_id', dup['id']).execute()
            print(f"[OK] Registros de @{dup['username']} removidos da fila de coleta.")
        except Exception as e:
            print(f"💥 Erro ao remover @{dup['username']} da fila de coleta: {e}")
            
    # 4. Confirmar se o oficial está na fila de coleta
    try:
        res_fila = supabase.table('fila_coleta').select('*').eq('candidato_id', oficial_username).execute()
        if not res_fila.data:
            print(f"[*] Adicionando registro oficial @{oficial_username} na fila de coleta...")
            supabase.table('fila_coleta').insert({
                'candidato_id': oficial_username,
                'status': 'PENDENTE',
                'prioridade': 10
            }).execute()
            print(f"[OK] @{oficial_username} inserido na fila de coleta.")
        else:
            print(f"[OK] Registro oficial @{oficial_username} já está presente na fila de coleta.")
    except Exception as e:
        print(f"💥 Erro ao validar/adicionar oficial na fila de coleta: {e}")
        
    print("\n[+] Processo de higienização cadastral de Guilherme Boulos finalizado com sucesso!")

if __name__ == '__main__':
    main()
