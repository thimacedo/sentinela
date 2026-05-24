import sys
import os
import uuid
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Reconfigura a saída do console no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    nome = "Janaina Paschoal"
    username = "janainacpaschoal"
    
    print(f"[*] Inserindo/Atualizando alvo: @{username} ({nome})")
    
    # 1. Verifica se já existe na tabela candidatos
    res = supabase.table('candidatos').select('id').eq('username', username).execute()
    
    if res.data:
        candidato_id = res.data[0]['id']
        print(f"[+] Alvo já existe na tabela candidatos com ID {candidato_id}. Atualizando status para Ativo.")
        supabase.table('candidatos').update({'status_monitoramento': 'Ativo', 'nome_completo': nome}).eq('id', candidato_id).execute()
    else:
        # Gera UUID para o novo candidato
        candidato_id = str(uuid.uuid4())
        print(f"[+] Alvo novo. Inserindo na tabela candidatos com ID {candidato_id}...")
        supabase.table('candidatos').insert({
            'id': candidato_id,
            'nome_completo': nome,
            'cargo': 'Não especificado',
            'username': username,
            'partido': 'N/A',
            'estado': 'SP',
            'status_monitoramento': 'Ativo'
        }).execute()
        
    print(f"[+] Inserindo na fila_coleta...")
    supabase.table('fila_coleta').upsert({
        'candidato_id': username,
        'status': 'PENDENTE',
        'prioridade': 1,
        'created_at': datetime.now(timezone.utc).isoformat()
    }, on_conflict="candidato_id,data_agendada", ignore_duplicates=True).execute()
    
    print("[OK] Alvo inserido com sucesso!")

if __name__ == '__main__':
    main()
