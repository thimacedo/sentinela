"""
Teste completo de coleta e classificação para o alvo lulaoficial.
Usa diretamente IGZyteWorker.fetch_comments_via_zyte() + ClassifierWorker.
"""
import asyncio
import sys
import os
import logging

# Garante que o diretório raiz do projeto está no PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from core.supabase_service import get_supabase_client
from workers.scrapers.ig_zyte import IGZyteWorker, Target

# Configura logging visível
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("test_lula")


async def main():
    target_username = "lulaoficial"
    db = get_supabase_client()

    # 1. Garante que o alvo existe no banco
    logger.info("=== PASSO 1: Garantindo alvo '%s' no banco ===", target_username)
    res = db.table('candidatos').upsert({
        "username": target_username,
        "status_monitoramento": "Ativo",
        "prioridade_coleta": 5
    }, on_conflict="username").execute()
    candidato_id = res.data[0]["id"] if res.data else None
    logger.info("Candidato ID: %s", candidato_id)

    # 2. Cria o worker Zyte com config mínima
    logger.info("=== PASSO 2: Instanciando IGZyteWorker ===")
    config = {
        "max_posts": 2,
        "max_comments_per_post": 20,
    }
    worker = IGZyteWorker(worker_id="test-lula", config=config)
    await worker.setup()

    # 3. Coleta direta (sem depender da fila)
    logger.info("=== PASSO 3: Coletando comentários via Zyte ===")
    target = Target(
        username=target_username,
        candidato_id=target_username,
        source="manual_test"
    )
    comments = await worker.fetch_comments_via_zyte(target)
    logger.info("Comentários extraídos: %d", len(comments))

    if not comments:
        logger.warning("Nenhum comentário encontrado. Verifique sessão/cookie.")
        await worker.teardown()
        return

    # 4. Persiste no banco
    logger.info("=== PASSO 4: Persistindo no Supabase ===")
    persist_stats = worker.persist_comments(target, comments)
    logger.info(
        "Inseridos: %d | Duplicados: %d | Falhas: %d",
        persist_stats.inserted, persist_stats.duplicated, persist_stats.failed
    )

    # 5. Classifica (até 10 por ciclo)
    logger.info("=== PASSO 5: Classificando via IA ===")
    classify_stats = await worker.classify_comments(persist_stats.inserted_ids)
    logger.info(
        "Classificados: %d | Falhas: %d",
        classify_stats.classified, classify_stats.failed
    )

    await worker.teardown()

    # 6. Resumo
    logger.info("=" * 60)
    logger.info("RESUMO FINAL")
    logger.info("  Alvo: @%s", target_username)
    logger.info("  Comentários extraídos: %d", len(comments))
    logger.info("  Inseridos no banco: %d", persist_stats.inserted)
    logger.info("  Duplicados: %d", persist_stats.duplicated)
    logger.info("  Classificados por IA: %d", classify_stats.classified)
    logger.info("  Falhas: %d", persist_stats.failed + classify_stats.failed)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
