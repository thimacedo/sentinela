# scripts/test_tiers.py

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workers.instagram_worker import InstagramWorker

async def test_individual_tier(tier_name: str, target: str, session_id: str):
    """Testa um tier específico."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTANDO {tier_name.upper()}")
    print(f"{'='*60}\n")
    
    from scripts.run_scrapy_spider import run_spider
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as tmp:
        output_path = tmp.name
    
    try:
        # Executa o spider
        run_spider(tier_name, target, session_id, "2", output_path)
        
        # Lê resultados
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                
            print(f"\n✅ {tier_name}: {len(data)} comentários extraídos")
            
            if data:
                print(f"\n📝 Exemplo:")
                print(f"  Autor: {data[0].get('ownerUsername')}")
                print(f"  Texto: {data[0].get('text')[:80]}...")
                print(f"  Tier: {data[0].get('tier_used')}")
        else:
            print(f"\n⚠️ {tier_name}: Nenhum dado extraído")
            
    except Exception as e:
        print(f"\n❌ {tier_name} FALHOU: {e}")
    finally:
        try:
            if os.path.exists(output_path):
                os.unlink(output_path)
        except:
            pass

async def test_full_system(target: str):
    """Testa o sistema completo de fallback."""
    print(f"\n{'='*60}")
    print(f"🚀 TESTE COMPLETO DO SISTEMA DE TIERS")
    print(f"{'='*60}\n")
    
    worker = InstagramWorker()
    
    print(f"Target: @{target}")
    
    # O Worker busca cookies automaticamente do Supabase
    success = worker.run(target)
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTADO FINAL")
    print(f"{'='*60}\n")
    
    if success:
        print(f"✅ Coleta para @{target} concluída com sucesso!")
    else:
        print(f"❌ Falha na coleta para @{target}.")

async def main():
    """Menu interativo."""
    print("""
╔══════════════════════════════════════════════════════════╗
║         🧪 TESTE DO SISTEMA TIER DE SCRAPING            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Configuração
    target = input("📍 Username do Instagram (ex: bolsonaro): ").strip()
    if not target:
        target = "bolsonaro"
    
    print("""
    Escolha o teste:
    
    1. Testar Tier 1 (API) isoladamente (Requer SessionID manual)
    2. Testar Tier 2 (DOM) isoladamente (Requer SessionID manual)
    3. Testar sistema completo com fallback (Usa cookies do DB)
    """)
    
    choice = input("Opção [1-3]: ").strip()
    
    if choice in ["1", "2"]:
        session_id = input("🔑 SessionID (cookie do Instagram): ").strip()
        if not session_id:
            print("\n❌ SessionID é obrigatório para testes isolados!")
            return
        
        spider = "instagram_api" if choice == "1" else "instagram_dom"
        await test_individual_tier(spider, target, session_id)
        
    elif choice == "3":
        await test_full_system(target)
    else:
        print("❌ Opção inválida")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
