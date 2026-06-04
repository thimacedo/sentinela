import os
import logging
from dotenv import load_dotenv
from core.supabase_service import get_supabase_client
from core.queue_manager import QueueManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_queue_pop")

load_dotenv()

db = get_supabase_client()
qm = QueueManager(db)

print("=== TESTANDO AUTO-REPOPULAÇÃO ===")

# Conta pendentes
count_res = db.table("fila_coleta").select("id", count="exact").eq("status", "PENDENTE").execute()
current_pending = count_res.count or 0
print(f"Pendentes atuais na fila: {current_pending}")

# Busca candidatos ativos
candidatos_res = db.table("candidatos")\
    .select("id,username,termometro,status_monitoramento")\
    .filter("status_monitoramento", "ilike", "Ativo")\
    .order("last_scraped_at", desc=False)\
    .limit(5).execute()

print(f"Candidatos ativos retornados para teste: {len(candidatos_res.data or [])}")
for c in candidatos_res.data or []:
    print(f" - @{c['username']} | Termômetro: {c['termometro']} | Status: {c['status_monitoramento']}")

# Roda a lógica de repopulação e exibe o que ocorre passo a passo
try:
    print("\nExecutando _ensure_queue_populated(min_pending=50)...")
    
    # 1. Busca candidatos ativos mais antigos para reinserir
    candidatos_res = db.table("candidatos")\
        .select("id,username,termometro")\
        .filter("status_monitoramento", "ilike", "Ativo")\
        .order("last_scraped_at", desc=False)\
        .limit(50).execute()

    reinseridos = 0
    for cand in (candidatos_res.data or []):
        username = cand.get("username")
        if not username:
            continue
        # Verifica se já existe na fila como PENDENTE
        check = db.table("fila_coleta")\
            .select("id")\
            .eq("candidato_id", cand["username"])\
            .eq("status", "PENDENTE")\
            .limit(1).execute()
        if check.data:
            print(f"  -> @{username} já está PENDENTE na fila.")
            continue

        termometro = cand.get("termometro", "MORNO")
        prioridade = 1 if termometro == "QUENTE" else (5 if termometro in ("FRIO", "MORNO") else 3)

        print(f"  -> Tentando upsert para @{username} (prioridade {prioridade})...")
        try:
            res_upsert = db.table("fila_coleta").upsert({
                "candidato_id": cand["username"],
                "status": "PENDENTE",
                "prioridade": prioridade,
            }, on_conflict="candidato_id,data_agendada").execute()
            print(f"     Sucesso! Retorno do banco: {res_upsert.data}")
            reinseridos += 1
        except Exception as e_upsert:
            print(f"     ❌ Erro no upsert de @{username}: {e_upsert}")

        if (current_pending + reinseridos) >= 50:
            break

    print(f"\nTotal reinseridos no teste: {reinseridos}")
except Exception as e:
    print(f"Erro geral: {e}")
