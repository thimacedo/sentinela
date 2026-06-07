import asyncio
from core.db import db_client

async def purge():
    print("🧹 [Purge] Limpando sugestões obsoletas (Fase 11)...")
    if not db_client.client:
        print("❌ [Purge] Erro: Supabase client não configurado.")
        return
        
    try:
        # Deleta todas as linhas da tabela worker_suggestions
        # Nota: Usamos um filtro que sempre é verdadeiro para limpar a tabela
        res = await asyncio.to_thread(
            db_client.client.table('worker_suggestions').delete().neq('status', 'DELETED_OR_NONEXISTENT').execute
        )
        print(f"✅ [Purge] {len(res.data) if res.data else 0} sugestões removidas.")
    except Exception as e:
        print(f"❌ [Purge] Falha ao limpar tabela: {e}")

if __name__ == "__main__":
    asyncio.run(purge())
