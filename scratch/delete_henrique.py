import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Reconfigura a saída do console no Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    username = "henriquealvesoficial"
    
    print(f"[*] Excluindo/inativando alvo: @{username}")
    
    # Busca o ID na tabela candidatos
    res = supabase.table('candidatos').select('id').eq('username', username).execute()
    
    if res.data:
        candidato_id = res.data[0]['id']
        print(f"[+] Alvo encontrado (ID {candidato_id}). Removendo da fila_coleta...")
        supabase.table('fila_coleta').delete().eq('candidato_id', username).execute()
        supabase.table('fila_coleta').delete().eq('candidato_id', candidato_id).execute()
        
        print(f"[+] Inativando na tabela candidatos...")
        supabase.table('candidatos').update({'status_monitoramento': 'Inativo'}).eq('id', candidato_id).execute()
        print("[OK] Alvo inativado com sucesso!")
    else:
        print(f"[-] Alvo @{username} não encontrado na tabela candidatos.")

if __name__ == '__main__':
    main()
