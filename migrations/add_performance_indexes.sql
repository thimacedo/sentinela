-- Sentinela Database Performance Optimizations
-- Created: 2026-07-05
-- Purpose: Add missing indexes to improve query performance

-- Index for fila_coleta table - frequently filtered by status
CREATE INDEX IF NOT EXISTS idx_fila_coleta_status ON fila_coleta(status);

-- Index for fila_coleta table - frequently ordered by prioridade and created_at
CREATE INDEX IF NOT EXISTS idx_fila_coleta_prioridade_created ON fila_coleta(prioridade DESC, created_at DESC);

-- Index for fila_coleta table - for atomic operations
CREATE INDEX IF NOT EXISTS idx_fila_coleta_status_locked ON fila_coleta(status, locked_by, locked_at);

-- Index for candidatos table - frequently filtered by status_monitoramento
CREATE INDEX IF NOT EXISTS idx_candidatos_status ON candidatos(status_monitoramento);

-- Index for candidatos table - frequently ordered by last_scraped_at
CREATE INDEX IF NOT EXISTS idx_candidatos_last_scraped ON candidatos(last_scraped_at DESC NULLS LAST);

-- Index for candidatos table - for the smart backoff query
CREATE INDEX IF NOT EXISTS idx_candidatos_termometro_last_scraped ON candidatos(termometro, last_scraped_at DESC NULLS LAST);

-- Composite index for the main query in _get_from_global_rotation
CREATE INDEX IF NOT EXISTS idx_candidatos_status_termometro_scraped ON 
    candidatos(status_monitoramento, termometro, last_scraped_at DESC NULLS LAST);

-- Index for fila_coleta table - for queue management
CREATE INDEX IF NOT EXISTS idx_fila_coleta_candidato_status ON fila_coleta(candidato_id, status);

-- Function to get candidates for scraping (replaces the vulnerable query)
CREATE OR REPLACE FUNCTION get_candidates_for_scraping(
    cold_threshold timestamp with time zone,
    hot_threshold timestamp with time zone,
    limit_count integer DEFAULT 20
) RETURNS SETOF candidatos AS $$
BEGIN
    RETURN QUERY
    SELECT id, username, termometro, last_scraped_at
    FROM candidatos
    WHERE status_monitoramento ILIKE 'Ativo'
    AND (
        last_scraped_at IS NULL
        OR (termometro = 'FRIO' AND last_scraped_at < cold_threshold)
        OR (termometro != 'FRIO' AND last_scraped_at < hot_threshold)
    )
    ORDER BY last_scraped_at ASC NULLS FIRST
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check and repopulate queue in a single query
CREATE OR REPLACE FUNCTION repopulate_queue_if_needed(
    min_pending integer DEFAULT 50
) RETURNS INTEGER AS $$
DECLARE
    current_pending integer;
    total_ativos integer;
    dynamic_min integer;
    candidates_to_insert jsonb[];
    inserted_count integer DEFAULT 0;
BEGIN
    -- Get current pending count
    SELECT COUNT(*) INTO current_pending
    FROM fila_coleta 
    WHERE status = 'PENDENTE';

    -- Get total active candidates
    SELECT COUNT(*) INTO total_ativos
    FROM candidatos 
    WHERE status_monitoramento ILIKE 'Ativo';

    -- Calculate dynamic minimum
    dynamic_min := GREATEST((total_ativos * 0.5)::integer, 10);

    IF current_pending >= dynamic_min THEN
        RETURN 0; -- Queue is healthy, nothing to do
    END IF;

    -- Find candidates not in queue to insert
    INSERT INTO fila_coleta (candidato_id, status, prioridade)
    SELECT 
        c.username,
        'PENDENTE'::text,
        CASE 
            WHEN c.termometro = 'QUENTE' THEN 1
            WHEN c.termometro IN ('FRIO', 'MORNO') THEN 5
            ELSE 3
        END
    FROM candidatos c
    WHERE c.status_monitoramento ILIKE 'Ativo'
    AND NOT EXISTS (
        SELECT 1 FROM fila_coleta q 
        WHERE q.candidato_id = c.username 
        AND q.status IN ('PENDENTE', 'EM_CURSO')
    )
    ORDER BY c.last_scraped_at ASC NULLS FIRST
    LIMIT min_pending;

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RETURN inserted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;