"""
PASA v37 - Auto Updater: Motor de auto-evolução do Nó Local.
Verifica diretivas remotas no Supabase e aplica atualizações de código ou configuração.
"""
import os
import sys
import subprocess
import json

# Garante que o diretório raiz do projeto esteja no Python Path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.supabase_service import get_supabase_client

def check_for_updates() -> bool:
    """Verifica se há novas diretivas ou atualizações de código no repositório."""
    try:
        db = get_supabase_client()
    except Exception as e:
        print(f"[AutoUpdater] Erro ao conectar ao Supabase: {e}")
        return False
        
    needs_restart = False

    # 1. Verifica Diretivas de Comando
    try:
        directives = db.table('system_directives').select('*').eq('executed', False).order('created_at').limit(1).execute()
        
        if directives.data:
            directive = directives.data[0]
            command = directive['command']
            payload = directive.get('payload', {})

            print(f"[AutoUpdater] Executando diretiva: {command}")

            if command == 'UPDATE_REPO':
                # Puxa as últimas melhorias do Git
                try:
                    flags = 0x08000000 if os.name == 'nt' else 0
                    subprocess.run(['git', 'pull', 'origin', 'main'], check=True, creationflags=flags)
                    # Verifica se o requirements.txt mudou e instala se necessário
                    if os.path.exists('requirements.txt'):
                        subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True, creationflags=flags)
                    needs_restart = True
                except Exception as e:
                    print(f"[AutoUpdater] Falha no git pull: {e}")

            elif command == 'CHANGE_CONFIG':
                # Atualiza configurações dinâmicas (ex: tempos de pausa)
                # Salva em um arquivo de config local que o local_server.py lê
                config_dir = os.path.join(project_root, 'data', 'cache')
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, 'runtime_config.json')
                
                with open(config_file, 'w') as f:
                    json.dump(payload, f)
                needs_restart = True
            
            elif command == 'RESTART':
                needs_restart = True

            # Marca como executado
            db.table('system_directives').update({'executed': True}).eq('id', directive['id']).execute()
            
    except Exception as e:
        print(f"[AutoUpdater] Erro ao verificar diretivas: {e}")

    return needs_restart

if __name__ == "__main__":
    check_for_updates()
