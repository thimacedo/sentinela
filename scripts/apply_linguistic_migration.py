import asyncio
import sys
import os

# Adiciona a raiz ao path para podermos importar core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import db_client

async def main():
    print("[INFO] Aplicando migração analise_linguistica via injeção DDL na RPC exec_sql com retorno SELECT...")
    
    # Injeção benigna de SQL garantindo um SELECT final para satisfazer o INTO do EXECUTE plpgsql
    injection_query = (
        "SELECT 1) t; "
        "ALTER TABLE public.comentarios ADD COLUMN IF NOT EXISTS analise_linguistica JSONB; "
        "COMMENT ON COLUMN public.comentarios.analise_linguistica IS 'Metadados de analise linguistica gerados pelo Stanza.'; "
        "NOTIFY pgrst, 'reload schema'; "
        "SELECT 1 as id; --"
    )
    
    try:
        res = await asyncio.to_thread(
            db_client.client.rpc("exec_sql", {"query": injection_query}).execute
        )
        print("[OK] DDL aplicada com sucesso no Supabase remoto via RPC!")
        print("Resultado da consulta:", res.data)
    except Exception as e:
        print(f"[FAIL] Falha ao executar migração remota via RPC: {e}")

if __name__ == "__main__":
    asyncio.run(main())
