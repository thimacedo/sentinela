-- migrations/add_queue_skip_locked.sql
-- PASA v88.0 — Fase F: Travas Atômicas na fila_coleta
-- Implementa SELECT FOR UPDATE SKIP LOCKED para suporte a clusters horizontais
-- múltiplos workers paralelos sem colisão no mesmo alvo.
--
-- Rollback: DROP FUNCTION IF EXISTS fila_coleta_claim_next;
--           DROP INDEX IF EXISTS idx_fila_coleta_status_prioridade;

BEGIN;

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  1. Índice composto para otimizar claim atômico             ║
-- ║  Cobre: status PENDENTE + prioridade ASC + created_at ASC  ║
-- ╚══════════════════════════════════════════════════════════════╝
CREATE INDEX IF NOT EXISTS idx_fila_coleta_status_prioridade
  ON fila_coleta (status, prioridade ASC, created_at ASC)
  WHERE status = 'PENDENTE';

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  2. Coluna de lock para rastreabilidade                     ║
-- ║  Registra qual worker está processando o item              ║
-- ╚══════════════════════════════════════════════════════════════╝
ALTER TABLE fila_coleta
  ADD COLUMN IF NOT EXISTS locked_by TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ DEFAULT NULL;

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  3. Função atômica de claim (SKIP LOCKED)                   ║
-- ║  Retorna UMA linha e a marca como EM_CURSO atomicamente.    ║
-- ║  Segura para múltiplos workers em paralelo.                 ║
-- ╚══════════════════════════════════════════════════════════════╝
CREATE OR REPLACE FUNCTION fila_coleta_claim_next(
  p_worker_id TEXT,
  p_max_prioridade INT DEFAULT 10
)
RETURNS TABLE (
  id            UUID,
  candidato_id  TEXT,
  prioridade    INT,
  status        TEXT,
  data_agendada DATE
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH candidato AS (
    SELECT fc.id
    FROM   fila_coleta fc
    WHERE  fc.status = 'PENDENTE'
      AND  fc.prioridade <= p_max_prioridade
      AND  fc.locked_by IS NULL          -- sem lock ativo
    ORDER BY fc.prioridade ASC, fc.created_at ASC
    LIMIT  1
    FOR UPDATE SKIP LOCKED              -- atômico, sem bloqueio
  )
  UPDATE fila_coleta fc
  SET
    status     = 'EM_CURSO',
    locked_by  = p_worker_id,
    locked_at  = NOW(),
    updated_at = NOW()
  FROM candidato
  WHERE fc.id = candidato.id
  RETURNING fc.id, fc.candidato_id, fc.prioridade, fc.status, fc.data_agendada;
END;
$$;

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  4. Função de liberação (release) após processamento        ║
-- ╚══════════════════════════════════════════════════════════════╝
CREATE OR REPLACE FUNCTION fila_coleta_release(
  p_queue_id  UUID,
  p_status    TEXT,    -- 'CONCLUIDO' | 'FALHA_SISTEMICA' | 'SEM_DADOS_RECENTES'
  p_worker_id TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE fila_coleta
  SET
    status     = p_status,
    locked_by  = NULL,
    locked_at  = NULL,
    updated_at = NOW()
  WHERE id        = p_queue_id
    AND locked_by = p_worker_id;  -- garantia de ownership
END;
$$;

-- ╔══════════════════════════════════════════════════════════════╗
-- ║  5. Função de auto-desbloqueio (timeout de lock)            ║
-- ║  Libera itens travados há mais de 30 min (worker crashou)  ║
-- ╚══════════════════════════════════════════════════════════════╝
CREATE OR REPLACE FUNCTION fila_coleta_release_stale(
  p_timeout_minutes INT DEFAULT 30
)
RETURNS INT  -- retorna quantos itens foram liberados
LANGUAGE plpgsql
AS $$
DECLARE
  v_count INT;
BEGIN
  UPDATE fila_coleta
  SET
    status     = 'PENDENTE',
    locked_by  = NULL,
    locked_at  = NULL,
    updated_at = NOW()
  WHERE status     = 'EM_CURSO'
    AND locked_at  < NOW() - (p_timeout_minutes || ' minutes')::INTERVAL;

  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END;
$$;

COMMIT;

-- Notifica PostgREST para recarregar schema
SELECT pg_notify('pgrst', 'reload schema');
