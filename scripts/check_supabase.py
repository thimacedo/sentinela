import asyncio
import os
import sys
import argparse
from dotenv import load_dotenv
from supabase import create_client, Client


def parse_filter(filter_str: str):
    """Transforma uma expressão como 'coluna=valor' em uma tupla (coluna, valor) para uso em .eq()."""
    if not filter_str:
        return None
    parts = filter_str.split('=', 1)
    if len(parts) != 2:
        raise ValueError('Filtro deve estar no formato coluna=valor')
    return parts[0].strip(), parts[1].strip()


async def check_supabase(table: str = "comentarios", filter_str: str = None):
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    print(f"🔍 [Check] URL: {url}")
    if not url or not key:
        print("❌ [Check] Credenciais ausentes no .env")
        return

    try:
        supabase: Client = create_client(url, key)
        print("✅ [Check] Cliente Supabase criado.")

        # Aplicar filtro se houver
        query = supabase.table(table).select('count', count='exact').limit(1)
        if filter_str:
            try:
                col, val = parse_filter(filter_str)
                query = query.eq(col, val)
            except Exception as e:
                print(f"⚠️ [Check] Falha ao analisar filtro '{filter_str}': {e}")
                return
        res = query.execute()
        print(f"✅ [Check] Tabela '{table}' acessível. Contagem: {res.count}")
    except Exception as e:
        print(f"❌ [Check] Erro ao acessar Supabase: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Verifica conectividade e contagem de registros no Supabase')
    parser.add_argument('--table', type=str, default='comentarios', help='Nome da tabela a ser verificada')
    parser.add_argument('--filter', type=str, default=None, help='Filtro no formato coluna=valor')
    args = parser.parse_args()
    asyncio.run(check_supabase(table=args.table, filter_str=args.filter))
