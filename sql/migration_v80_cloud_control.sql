-- ============================================================
-- MIGRAÇÃO v80.0 — Sentinela Cloud Control & Autonomia Total
-- Executar no SQL Editor do Supabase
-- ============================================================

-- 1. Heartbeat do sistema (prova de vida local/cloud)
CREATE TABLE IF NOT EXISTS system_heartbeat (
    id          BIGSERIAL PRIMARY KEY,
    source      TEXT NOT NULL CHECK (source IN ('local', 'cloud_actions', 'cloud_render')),
    worker_id   TEXT,
    worker_cycle INT,
    status      TEXT DEFAULT 'ok',
    metadata    JSONB,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para consulta rápida do heartbeat mais recente
CREATE UNIQUE INDEX IF NOT EXISTS idx_heartbeat_source ON system_heartbeat (source);

-- RLS: Leitura pública (frontend), escrita apenas via service key
ALTER TABLE system_heartbeat ENABLE ROW LEVEL SECURITY;
CREATE POLICY "heartbeat_public_read" ON system_heartbeat FOR SELECT USING (true);
CREATE POLICY "heartbeat_service_write" ON system_heartbeat FOR ALL USING (auth.role() = 'service_role');

-- 2. Comandos remotos (controle via interface web)
CREATE TABLE IF NOT EXISTS system_commands (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command     TEXT NOT NULL CHECK (command IN ('PAUSE', 'RESUME', 'RESTART', 'UPDATE', 'FORCE_SCRAPE')),
    target      TEXT,           -- alvo específico (ex: username) ou NULL para comando global
    issued_by   TEXT,           -- identificador do operador
    issued_at   TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    status      TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'executing', 'done', 'failed')),
    result      TEXT
);

-- RLS: Escrita autenticada, leitura service role
ALTER TABLE system_commands ENABLE ROW LEVEL SECURITY;
CREATE POLICY "commands_authenticated_write" ON system_commands FOR INSERT WITH CHECK (true);
CREATE POLICY "commands_service_read" ON system_commands FOR SELECT USING (auth.role() = 'service_role' OR auth.role() = 'authenticated');

-- 3. Auditoria de eventos do sistema
CREATE TABLE IF NOT EXISTS system_events (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL, -- 'autopilot_intervention', 'session_healer', 'queue_repopulated', 'hotfix_applied'
    source      TEXT,          -- 'local', 'cloud_actions'
    severity    TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    description TEXT,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events (event_type, created_at DESC);

-- RLS
ALTER TABLE system_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "events_public_read" ON system_events FOR SELECT USING (true);
CREATE POLICY "events_service_write" ON system_events FOR ALL USING (auth.role() = 'service_role');

-- 4. Campos de locking atômico na fila_coleta (evita colisão local/cloud)
ALTER TABLE fila_coleta
    ADD COLUMN IF NOT EXISTS locked_by    TEXT,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_fila_coleta_lock ON fila_coleta (status, locked_until)
    WHERE status = 'PENDENTE';

-- Função helper para claim atômico (evita race condition)
CREATE OR REPLACE FUNCTION claim_fila_target(p_worker_id TEXT, p_lock_minutes INT DEFAULT 20)
RETURNS TABLE(id UUID, username TEXT, candidato_id TEXT, prioridade INT) AS $$
DECLARE
    v_id UUID;
BEGIN
    -- Seleciona e bloqueia atomicamente um item pendente não bloqueado
    SELECT fc.id INTO v_id
    FROM fila_coleta fc
    WHERE fc.status = 'PENDENTE'
      AND (fc.locked_until IS NULL OR fc.locked_until < NOW())
    ORDER BY fc.prioridade ASC, fc.created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF v_id IS NULL THEN
        RETURN;
    END IF;

    UPDATE fila_coleta
    SET locked_by = p_worker_id,
        locked_until = NOW() + (p_lock_minutes || ' minutes')::INTERVAL
    WHERE fila_coleta.id = v_id;

    RETURN QUERY
    SELECT fc.id, fc.candidato_id AS username, fc.candidato_id, fc.prioridade
    FROM fila_coleta fc WHERE fc.id = v_id;
END;
$$ LANGUAGE plpgsql;
