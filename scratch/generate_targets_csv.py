import sys
import os
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.supabase_service import get_supabase_client

def main():
    supabase = get_supabase_client()
    csv_filename = 'alvos_sanitizacao.csv'
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', csv_filename))
    
    print("[*] Buscando todos os alvos cadastrados no Supabase...")
    try:
        # Faz select de todos os candidatos sem limite ou com paginação se for muito grande
        # Normalmente o Supabase restringe a 1000 registros por query, vamos trazer em blocos se necessário.
        # Vamos verificar o total aproximado. Se for menos de 1000, um único select resolve.
        res = supabase.table('candidatos').select('id, nome_completo, cargo, username, status_monitoramento').execute()
        alvos = res.data or []
        print(f"[+] Recuperados {len(alvos)} alvos do banco de dados.")
        
        print(f"[*] Gerando arquivo CSV em: {csv_path}...")
        
        # Abre o arquivo com encoding UTF-8 com assinatura (BOM) para o Excel ler acentos perfeitamente no Windows
        with open(csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Cabeçalho
            writer.writerow(['id', 'nome_completo', 'cargo', 'username', 'status_monitoramento'])
            
            # Dados
            for alvo in alvos:
                writer.writerow([
                    alvo.get('id', ''),
                    alvo.get('nome_completo', ''),
                    alvo.get('cargo', ''),
                    alvo.get('username', ''),
                    alvo.get('status_monitoramento', '')
                ])
                
        print(f"[OK] Arquivo '{csv_filename}' gerado com sucesso!")
        
    except Exception as e:
        print(f"💥 Erro ao gerar o CSV: {e}")

if __name__ == '__main__':
    main()
