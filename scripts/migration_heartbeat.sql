-- ============================================================
-- Migration: Sentinela Heartbeat (v98.2)
-- Objetivo: Detectar paradas de coleta automaticamente
--           via pg_cron e registrar em system_events
-- ============================================================

-- 1. Garante colunas extras na tabela system_events (se não existirem)
ALTER TABLE system_events
    ADD COLUMN IF NOT EXISTS metadata  jsonb,
    ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();

-- 2. Habilita a extensão pg_cron (já disponível no Supabase)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- 3. Remove job anterior se existir (idempotente)
SELECT cron.unschedule('sentinela_heartbeat_check')
WHERE EXISTS (
    SELECT 1 FROM cron.job WHERE jobname = 'sentinela_heartbeat_check'
);

-- 4. Registra o job: roda a cada 30 minutos
SELECT cron.schedule(
    'sentinela_heartbeat_check',
    '*/30 * * * *',
    $$
    DO $$
    DECLARE
        v_ultima_coleta  timestamptz;
        v_gap_min        numeric;
        v_max_gap_min    int := 15;  -- máximo de minutos tolerado sem coleta
    BEGIN
        SELECT MAX(data_coleta) INTO v_ultima_coleta FROM comentarios;
        v_gap_min := EXTRACT(EPOCH FROM (now() - v_ultima_coleta)) / 60.0;

        IF v_gap_min > v_max_gap_min THEN
            INSERT INTO system_events (
                event_type, source, severity, description, metadata, created_at
            ) VALUES (
                'COLETA_PARADA',
                'pg_cron_heartbeat',
                'critical',
                format(
                    'Coleta parada há %.0f minutos. Última: %s',
                    v_gap_min,
                    to_char(v_ultima_coleta AT TIME ZONE 'America/Recife', 'DD/MM HH24:MI')
                ),
                jsonb_build_object(
                    'gap_minutes',    round(v_gap_min),
                    'ultima_coleta',  v_ultima_coleta,
                    'max_gap_min',    v_max_gap_min,
                    'trigger',        'pg_cron'
                ),
                now()
            )
            -- Evita duplicatas: só insere se não há evento nos últimos 25min
            ON CONFLICT DO NOTHING;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    $$
);

-- 5. Índice para leitura eficiente pelo SRE Agent
CREATE INDEX IF NOT EXISTS idx_system_events_type_created
    ON system_events (event_type, created_at DESC);
