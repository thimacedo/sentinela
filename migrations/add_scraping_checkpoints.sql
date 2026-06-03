-- migrations/add_scraping_checkpoints.sql
-- PASA v88.0 — Fase G: Checkpoints Intra-Cycle para InstagramScraperWorker
-- Permite retomar raspagemde um perfil no último post salvo após crash,
-- sem perda de dados e sem duplicação.
--
-- Rollback:
--   DROP TABLE IF EXISTS scraping_checkpoints;
--   DROP FUNCTION IF EXISTS upsert_scraping_checkpoint;
--   DROP FUNCTION IF EXISTS clear_scraping_checkpoint;

BEGIN;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║  Tabela de Checkpoints de Raspagem                               ║
-- ║  Uma linha por (worker_id, candidato_id) ativo.                 ║
-- ║  Salva o último post_shortcode processado e métricas do ciclo.  ║
-- ╚═══════════════════════════════════════════════════════════════════╝
CREATE TABLE IF NOT EXISTS scraping_checkpoints (
  id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  worker_id       TEXT        NOT NULL,
  candidato_id    TEXT        NOT NULL,

  -- Último post completamente salvo no banco
  last_shortcode  TEXT        NOT NULL,
  -- Total de posts processados neste ciclo até agora
  posts_done      INT         DEFAULT 0,
  -- Total de comentários inseridos neste ciclo até agora
  comments_done   INT         DEFAULT 0,

  -- Estado do ciclo
  cycle_started_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW(),

  -- Constraint: um checkpoint por (worker, candidato) ativo
  UNIQUE (worker_id, candidato_id)
);

-- Índice para busca rápida por candidato
CREATE INDEX IF NOT EXISTS idx_checkpoints_candidato
  ON scraping_checkpoints (candidato_id);

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║  Função de upsert idempotente                                    ║
-- ╚═══════════════════════════════════════════════════════════════════╝
CREATE OR REPLACE FUNCTION upsert_scraping_checkpoint(
  p_worker_id       TEXT,
  p_candidato_id    TEXT,
  p_last_shortcode  TEXT,
  p_posts_done      INT,
  p_comments_done   INT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO scraping_checkpoints
    (worker_id, candidato_id, last_shortcode, posts_done, comments_done, updated_at)
  VALUES
    (p_worker_id, p_candidato_id, p_last_shortcode, p_posts_done, p_comments_done, NOW())
  ON CONFLICT (worker_id, candidato_id)
  DO UPDATE SET
    last_shortcode = EXCLUDED.last_shortcode,
    posts_done     = EXCLUDED.posts_done,
    comments_done  = EXCLUDED.comments_done,
    updated_at     = NOW();
END;
$$;

-- ╔═══════════════════════════════════════════════════════════════════╗
-- ║  Função de limpeza após ciclo completo                          ║
-- ╚═══════════════════════════════════════════════════════════════════╝
CREATE OR REPLACE FUNCTION clear_scraping_checkpoint(
  p_worker_id    TEXT,
  p_candidato_id TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  DELETE FROM scraping_checkpoints
  WHERE worker_id    = p_worker_id
    AND candidato_id = p_candidato_id;
END;
$$;

COMMIT;

SELECT pg_notify('pgrst', 'reload schema');
