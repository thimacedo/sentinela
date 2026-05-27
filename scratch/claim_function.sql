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
    SELECT fc.id, fc.username, fc.candidato_id, fc.prioridade
    FROM fila_coleta fc WHERE fc.id = v_id;
END;
$$ LANGUAGE plpgsql;
