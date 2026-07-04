import asyncio
import os
import sys
from core.supabase_client import get_supabase_client
from core.instagram_scraper_v2 import InstagramScraperV2

# Ajusta encoding no Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

async def main():
    from dotenv import load_dotenv
    load_dotenv()
    print("🔄 [Recuperacao] Iniciando saneamento do sistema...")
    db = get_supabase_client()
    
    # 1. Limpa todos os itens travados/bloqueados na fila no Supabase remoto
    print("🧹 Limpando locks da fila de coleta (Supabase)...")
    try:
        # Força alvos travados em EM_CURSO ou com erros temporários a voltar a PENDENTE
        res = db.table("fila_coleta").update({
            "status": "PENDENTE", 
            "locked_by": None, 
            "locked_at": None
        }).neq("status", "CONCLUIDO").execute()
        print("✅ Itens na fila resetados para PENDENTE com sucesso.")
    except Exception as e:
        print(f"⚠️ Falha ao resetar fila: {e}")
        
    # 2. Reseta checkpoints antigos de coleta incompleta para evitar travamento cognitivo
    print("🧹 Limpando checkpoints de scraping pendentes...")
    try:
        db.table("scraping_checkpoints").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("✅ Checkpoints limpos.")
    except Exception as e:
        print(f"⚠️ Falha ao limpar checkpoints: {e}")
        
    # 3. Testa integridade de cada sessão do Instagram cadastrada
    print("🔑 Testando integridade do pool de sessoes...")
    try:
        scraper = InstagramScraperV2()
        print(f"ℹ️ {len(scraper.sessions)} sessões carregadas no pool.")
        for s in scraper.sessions:
            status_desc = "Disponivel" if s.is_available else "Bloqueada"
            print(f"   - {s.label}: {status_desc} (Erro anterior: {getattr(s, 'last_error', 'Nenhum')})")
    except Exception as e:
        print(f"⚠️ Falha ao inspecionar sessões: {e}")
        
    print("🚀 [Recuperacao] Concluida. Fila limpa e pronta para novos alvos.")

if __name__ == "__main__":
    asyncio.run(main())
