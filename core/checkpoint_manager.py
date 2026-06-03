"""
core/checkpoint_manager.py
PASA v88.0 — Fase G: Gerenciador de Checkpoints Intra-Cycle

Permite que o InstagramScraperWorker (e outros workers) salvem o progresso
a cada post processado, possibilitando retomada após crash sem perda de dados.

Uso típico:
    cp = CheckpointManager(db_client, worker_id='ig_worker_1', candidato_id='username')
    checkpoint = cp.load()  # None se não há checkpoint
    if checkpoint:
        logger.info(f"Retomando do post {checkpoint['last_shortcode']}")

    # Por post processado:
    cp.save(last_shortcode='ABC123', posts_done=3, comments_done=150)

    # Ao finalizar o ciclo com sucesso:
    cp.clear()
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("checkpoint_manager")


class CheckpointManager:
    """
    Gerencia checkpoints de raspagem no Supabase.
    Interface simples: load / save / clear.
    Operações idempotentes via funções SQL (upsert seguro).
    Degrada graciosamente se a tabela ainda não existe (migração pendente).
    """

    def __init__(self, db_client, worker_id: str, candidato_id: str):
        self.db = db_client
        self.worker_id = worker_id
        self.candidato_id = candidato_id
        self._available: Optional[bool] = None  # cache de disponibilidade

    def _is_available(self) -> bool:
        """Verifica se a tabela de checkpoints existe no banco (cache após 1ª chamada)."""
        if self._available is not None:
            return self._available
        try:
            self.db.table("scraping_checkpoints").select("id").limit(1).execute()
            self._available = True
        except Exception:
            self._available = False
            logger.debug(
                "[Checkpoint] Tabela 'scraping_checkpoints' indisponível. "
                "Execute migrations/add_scraping_checkpoints.sql no Supabase."
            )
        return self._available

    def load(self) -> Optional[dict]:
        """
        Carrega o checkpoint mais recente para este (worker_id, candidato_id).
        Retorna dict com {last_shortcode, posts_done, comments_done} ou None.
        """
        if not self._is_available():
            return None
        try:
            res = (
                self.db.table("scraping_checkpoints")
                .select("last_shortcode, posts_done, comments_done, updated_at")
                .eq("worker_id", self.worker_id)
                .eq("candidato_id", self.candidato_id)
                .limit(1)
                .execute()
            )
            if res.data:
                cp = res.data[0]
                logger.info(
                    "[Checkpoint] Checkpoint encontrado para @%s | último_post=%s | posts=%d | comentários=%d",
                    self.candidato_id,
                    cp.get("last_shortcode"),
                    cp.get("posts_done", 0),
                    cp.get("comments_done", 0),
                )
                return cp
        except Exception as e:
            logger.warning("[Checkpoint] Erro ao carregar checkpoint para @%s: %s", self.candidato_id, e)
        return None

    def save(
        self,
        last_shortcode: str,
        posts_done: int,
        comments_done: int,
    ) -> bool:
        """
        Salva (upsert) o checkpoint atual.
        Retorna True se bem-sucedido, False em caso de falha (não bloqueia o ciclo).
        """
        if not self._is_available():
            return False
        try:
            self.db.rpc("upsert_scraping_checkpoint", {
                "p_worker_id":      self.worker_id,
                "p_candidato_id":   self.candidato_id,
                "p_last_shortcode": last_shortcode,
                "p_posts_done":     posts_done,
                "p_comments_done":  comments_done,
            }).execute()
            logger.debug(
                "[Checkpoint] Salvo para @%s | post=%s | posts=%d | comentários=%d",
                self.candidato_id, last_shortcode, posts_done, comments_done,
            )
            return True
        except Exception as e:
            logger.warning("[Checkpoint] Erro ao salvar checkpoint para @%s: %s", self.candidato_id, e)
            return False

    def clear(self) -> bool:
        """
        Remove o checkpoint após ciclo bem-sucedido.
        Retorna True se bem-sucedido.
        """
        if not self._is_available():
            return False
        try:
            self.db.rpc("clear_scraping_checkpoint", {
                "p_worker_id":    self.worker_id,
                "p_candidato_id": self.candidato_id,
            }).execute()
            logger.debug("[Checkpoint] Removido para @%s após ciclo completo.", self.candidato_id)
            return True
        except Exception as e:
            # Fallback via DELETE direto
            try:
                self.db.table("scraping_checkpoints").delete().eq(
                    "worker_id", self.worker_id
                ).eq("candidato_id", self.candidato_id).execute()
                return True
            except Exception:
                logger.warning("[Checkpoint] Erro ao limpar checkpoint para @%s: %s", self.candidato_id, e)
                return False
