"""
cloud_scrape_cycle.py — Worker de Coleta Cloud para GitHub Actions (PASA v80.0)

Versão simplificada do main_runner para ambientes cloud efêmeros.
Sem Watchdog, sem AutopilotManager, sem SQLite.
Execução única com timeout global de 45 minutos.

Uso:
  python scripts/cloud_scrape_cycle.py [--max-targets N] [--max-posts N]
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
import argparse
from datetime import datetime, timezone

# --- Auto-Anchoring ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# Configura encoding para CI
if sys.platform == "win32" or os.getenv("GITHUB_ACTIONS"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cloud_scrape_cycle")

# Timeout global: 45 minutos (GitHub Actions tem limite de 6h mas queremos ciclos curtos)
GLOBAL_TIMEOUT_SECONDS = 45 * 60
START_TIME = time.time()


def time_remaining() -> float:
    return max(0, GLOBAL_TIMEOUT_SECONDS - (time.time() - START_TIME))


async def run_cloud_cycle(max_targets: int = 5, max_posts: int = 2, max_comments: int = 30):
    """
    Ciclo único de coleta para ambiente cloud.
    Coleta alvos prioritários e grava diretamente no Supabase.
    """
    logger.info(f"☁️ [CloudScrape] Iniciando ciclo cloud (max_targets={max_targets}, max_posts={max_posts})")
    logger.info(f"☁️ [CloudScrape] Tempo disponível: {time_remaining()/60:.1f} min")

    from core.supabase_service import get_supabase_client
    from core.instagram_scraper_v2 import InstagramScraperV2
    from core.ai_service import ai_service, clean_null_chars
    from core.lexical_filter import lexical_filter
    from core.behavior_engine import behavior_engine

    db = get_supabase_client()

    # Publica heartbeat de início no Supabase
    try:
        db.table("system_heartbeat").upsert({
            "source": "cloud_actions",
            "status": "running",
            "metadata": {"started_at": datetime.now(timezone.utc).isoformat()},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="source").execute()
    except Exception as e:
        logger.warning(f"⚠️ Falha no heartbeat inicial: {e}")

    # Busca alvos prioritários (com locking atômico via função SQL)
    targets_scraped = 0
    total_inserted = 0
    errors = []

    try:
        # Usa a função PostgreSQL de claim atômico para evitar colisão com worker local
        pending_res = db.rpc("claim_fila_target", {
            "p_worker_id": "cloud_actions",
            "p_lock_minutes": 30
        }).execute()
        targets_data = pending_res.data or []
    except Exception:
        # Fallback se a função SQL não existir ainda
        logger.warning("⚠️ Função claim_fila_target não encontrada. Usando query direta.")
        pending_res = db.table("fila_coleta")\
            .select("id,username,candidato_id,prioridade")\
            .eq("status", "PENDENTE")\
            .is_("locked_by", "null")\
            .order("prioridade", desc=False)\
            .limit(max_targets)\
            .execute()
        targets_data = pending_res.data or []

    if not targets_data:
        logger.info("☁️ [CloudScrape] Nenhum alvo pendente na fila. Encerrando.")
        _finalize_heartbeat(db, targets_scraped, total_inserted, errors)
        return

    logger.info(f"☁️ [CloudScrape] {len(targets_data)} alvo(s) selecionado(s).")
    scraper = InstagramScraperV2(headless=True, max_retries=2)

    for target_row in targets_data[:max_targets]:
        if time_remaining() < 300:  # Menos de 5 min restantes → para
            logger.warning("⏰ [CloudScrape] Timeout se aproximando. Encerrando coleta.")
            break

        username = target_row.get("username") or target_row.get("candidato_id", "")
        queue_id = target_row.get("id")

        if not username:
            continue

        logger.info(f"🎯 [CloudScrape] Coletando @{username}...")

        try:
            scrape_data = await scraper.scrape_profile(
                username=username,
                candidato_id=username,
                max_posts=max_posts,
                max_comments_per_post=max_comments,
                max_age_days=7
            )

            comments = scrape_data.get("comments", []) if isinstance(scrape_data, dict) else scrape_data or []

            # Pipeline de qualidade
            if comments:
                comments = lexical_filter.filter_list(comments)
                comments = behavior_engine.detect_coordinated_clusters(comments)

            if not comments:
                logger.info(f"⏭️ [CloudScrape] @{username}: sem comentários novos.")
                _mark_queue_done(db, queue_id, "SEM_DADOS_RECENTES")
                continue

            # Persistência direta no Supabase (sem SQLite em cloud)
            safe_comments = [{
                "id_externo": c.get("id_externo"),
                "texto_bruto": c.get("texto_bruto"),
                "autor_username": c.get("autor_username"),
                "data_publicacao": c.get("data_publicacao"),
                "data_coleta": c.get("data_coleta"),
                "candidato_id": c.get("candidato_id"),
                "post_shortcode": c.get("post_shortcode"),
                "plataforma": c.get("plataforma", "INSTAGRAM"),
                "processado_ia": False,
                "tier_used": c.get("tier_used", 2),
                "fonte_coleta": "cloud_actions",
            } for c in comments]

            res = db.table("comentarios").upsert(
                clean_null_chars(safe_comments),
                on_conflict="candidato_id,post_shortcode,id_externo",
                ignore_duplicates=True
            ).execute()

            inserted = len(res.data) if res.data else 0
            total_inserted += inserted
            targets_scraped += 1
            logger.info(f"✅ [CloudScrape] @{username}: {len(comments)} extraídos, {inserted} novos.")

            _mark_queue_done(db, queue_id, "CONCLUIDO")

            # Jitter entre alvos para não sobrecarregar o Instagram
            import random
            await asyncio.sleep(random.uniform(15, 30))

        except Exception as e:
            err_msg = str(e)[:150]
            logger.error(f"💥 [CloudScrape] Erro em @{username}: {err_msg}")
            errors.append(err_msg)
            _mark_queue_done(db, queue_id, "PENDENTE")  # Devolve à fila

    logger.info(f"☁️ [CloudScrape] Ciclo encerrado: {targets_scraped} alvos, {total_inserted} inserções.")
    _finalize_heartbeat(db, targets_scraped, total_inserted, errors)


def _mark_queue_done(db, queue_id, status: str):
    """Atualiza o status do item na fila e libera o lock."""
    if not queue_id:
        return
    try:
        db.table("fila_coleta").update({
            "status": status,
            "locked_by": None,
            "locked_until": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", queue_id).execute()
    except Exception as e:
        logger.warning(f"⚠️ Erro ao atualizar fila (ID: {queue_id}): {e}")


def _finalize_heartbeat(db, scraped: int, inserted: int, errors: list):
    """Publica heartbeat final no Supabase."""
    try:
        db.table("system_heartbeat").upsert({
            "source": "cloud_actions",
            "status": "done",
            "metadata": {
                "targets_scraped": scraped,
                "total_inserted": inserted,
                "errors": errors[:5],
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": round(time.time() - START_TIME, 1),
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="source").execute()
    except Exception as e:
        logger.warning(f"⚠️ Falha no heartbeat final: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Ciclo de coleta cloud Sentinela")
    parser.add_argument("--max-targets", type=int, default=5, help="Número máximo de alvos por ciclo")
    parser.add_argument("--max-posts", type=int, default=2, help="Máximo de posts por alvo")
    parser.add_argument("--max-comments", type=int, default=30, help="Máximo de comentários por post")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_cloud_cycle(
        max_targets=args.max_targets,
        max_posts=args.max_posts,
        max_comments=args.max_comments,
    ))
