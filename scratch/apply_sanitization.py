import sys
import os
import csv
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Reconfigura a saída do console no Windows para evitar falhas com emojis e acentos
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    csv_filename = 'alvos_sanitizacao.csv'
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', csv_filename))
    
    if not os.path.exists(csv_path):
        print(f"❌ Erro: Arquivo '{csv_filename}' não encontrado em {csv_path}")
        return
        
    print(f"[*] Lendo edições do arquivo '{csv_filename}'...")
    csv_records = {}
    
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            record_id = row.get('id')
            if record_id:
                csv_records[record_id.strip()] = {
                    'nome_completo': row.get('nome_completo', '').strip(),
                    'cargo': row.get('cargo', '').strip(),
                    'username': row.get('username', '').strip().replace('@', ''),
                    'status_monitoramento': row.get('status_monitoramento', '').strip()
                }
                
    print(f"[+] Total de registros no CSV: {len(csv_records)}")
    
    print("[*] Buscando registros atuais do Supabase para comparação...")
    try:
        res = supabase.table('candidatos').select('id, nome_completo, cargo, username, status_monitoramento').execute()
        db_records = {item['id']: item for item in res.data or []}
        print(f"[+] Total de registros no banco: {len(db_records)}")
        
        updates_count = 0
        inactivations_count = 0
        fila_updates_count = 0
        
        # 1. Processar registros que estão no banco
        for db_id, db_item in db_records.items():
            # Caso A: O registro foi removido do CSV -> Inativar no banco
            if db_id not in csv_records:
                if db_item.get('status_monitoramento') == 'Ativo':
                    print(f"[-] Alvo removido do CSV (Será inativado): @{db_item.get('username')} ({db_item.get('nome_completo')})")
                    # Inativa no banco
                    supabase.table('candidatos').update({'status_monitoramento': 'Inativo'}).eq('id', db_id).execute()
                    # Remove da fila de coleta
                    supabase.table('fila_coleta').delete().eq('candidato_id', db_item.get('username')).execute()
                    supabase.table('fila_coleta').delete().eq('candidato_id', db_id).execute()
                    inactivations_count += 1
                continue
                
            # Caso B: O registro está em ambos -> Comparar e atualizar se houver diferenças
            csv_item = csv_records[db_id]
            diff = {}
            
            for field in ['nome_completo', 'cargo', 'username', 'status_monitoramento']:
                csv_val = csv_item[field]
                db_val = db_item.get(field) or ''
                if csv_val != db_val:
                    diff[field] = (db_val, csv_val)
                    
            if diff:
                print(f"\n[*] Modificação detectada para ID {db_id} (@{db_item.get('username')}):")
                update_payload = {}
                for field, (old_val, new_val) in diff.items():
                    print(f"  - {field}: '{old_val}' -> '{new_val}'")
                    update_payload[field] = new_val
                
                # Se o username vai mudar, removemos a dependência de chave estrangeira da fila_coleta ANTES
                if 'username' in update_payload:
                    old_username = db_item.get('username')
                    print(f"  [*] Removendo dependência da fila_coleta para @{old_username} (Prevenção de restrição FK)...")
                    supabase.table('fila_coleta').delete().eq('candidato_id', old_username).execute()
                    supabase.table('fila_coleta').delete().eq('candidato_id', db_id).execute()
                
                # Executa o update no candidato
                supabase.table('candidatos').update(update_payload).eq('id', db_id).execute()
                updates_count += 1
                
                # Se o status_monitoramento mudou para Inativo
                if 'status_monitoramento' in update_payload and update_payload['status_monitoramento'] == 'Inativo':
                    print(f"  [-] Inativando na fila de coleta...")
                    supabase.table('fila_coleta').delete().eq('candidato_id', db_item.get('username')).execute()
                    supabase.table('fila_coleta').delete().eq('candidato_id', db_id).execute()
                    fila_updates_count += 1
                
                # Se o username mudou (ou status foi ativado) e continua ativo
                elif ('username' in update_payload or 'status_monitoramento' in update_payload) and csv_item['status_monitoramento'] == 'Ativo':
                    new_username = csv_item['username']
                    print(f"  [+] Sincronizando novo username @{new_username} na fila de coleta...")
                    
                    # Garante a inserção do novo username na fila
                    supabase.table('fila_coleta').upsert({
                        'candidato_id': new_username,
                        'status': 'PENDENTE',
                        'prioridade': 1,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }, on_conflict="candidato_id,data_agendada", ignore_duplicates=True).execute()
                    fila_updates_count += 1
                    
                # Se apenas outros campos mudaram, mas o status é Ativo e o username mudou de caixa, garante inserção
                elif 'username' in update_payload and csv_item['status_monitoramento'] == 'Ativo':
                    new_username = csv_item['username']
                    supabase.table('fila_coleta').upsert({
                        'candidato_id': new_username,
                        'status': 'PENDENTE',
                        'prioridade': 1,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }, on_conflict="candidato_id,data_agendada", ignore_duplicates=True).execute()
                    fila_updates_count += 1

        print("\n--- Relatório Final da Sanitização ---")
        print(f"[OK] Total de alvos inativados (removidos do CSV): {inactivations_count}")
        print(f"[OK] Total de alvos atualizados com modificações: {updates_count}")
        print(f"[OK] Total de sincronizações feitas na fila de coleta: {fila_updates_count}")
        print("[+] Sincronização concluída com sucesso!")

    except Exception as e:
        print(f"💥 Erro na sincronização: {e}")

if __name__ == '__main__':
    main()
