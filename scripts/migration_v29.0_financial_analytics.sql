-- =======================================================
-- Migration v29.0 - Analytics Financeiro e Auditoria Cloud
-- Objetivo: Prover insights de gastos por alvo e provedor
-- =======================================================

-- 1. Criar View para Analytics de Gastos por Provedor
CREATE OR REPLACE VIEW view_spending_by_provider AS
SELECT 
    provider,
    status,
    count(*) as total_calls,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_calls,
    SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as error_calls,
    AVG(CAST(payload->>'text_length' AS INTEGER)) as avg_text_length
FROM fallback_logs
GROUP BY provider, status;

-- 2. RPC para obter gastos por Candidato/Alvo
-- Baseia-se no candidato_id extraído do payload
CREATE OR REPLACE FUNCTION get_spending_by_target()
RETURNS TABLE (
    candidato_id TEXT,
    total_calls BIGINT,
    estimated_tokens BIGINT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        payload->>'candidato_id' as candidato_id,
        count(*) as total_calls,
        SUM(CAST(payload->>'text_length' AS INTEGER)) / 4 as estimated_tokens -- Estimativa: 1 token ~ 4 caracteres
    FROM fallback_logs
    WHERE payload->>'candidato_id' IS NOT NULL
    GROUP BY payload->>'candidato_id'
    ORDER BY total_calls DESC;
END;
$$;

-- 3. RPC para Resumo de Erros Cloud (Auditoria de Resiliência)
CREATE OR REPLACE FUNCTION get_cloud_error_summary()
RETURNS TABLE (
    provider TEXT,
    error_type TEXT,
    error_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.provider,
        l.payload->>'error_type' as error_type,
        count(*) as error_count
    FROM fallback_logs l
    WHERE l.status = 'ERROR'
    GROUP BY l.provider, l.payload->>'error_type'
    ORDER BY error_count DESC;
END;
$$;
