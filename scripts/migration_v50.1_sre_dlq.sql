-- Migração PASA v50.1: Criação da Tabela de Dead Letter Queue (fila_dlq)
-- Arquivo: scripts/migration_v50.1_sre_dlq.sql

CREATE TABLE IF NOT EXISTS public.fila_dlq (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_target_id UUID NULL,
    queue_id UUID NULL,
    target_username VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL DEFAULT 'INSTAGRAM',
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NULL,
    stack_trace TEXT NULL,
    code_version VARCHAR(20) NOT NULL DEFAULT 'v100.0',
    retry_count INT NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Permissões de RLS para fila_dlq (padrão do projeto)
ALTER TABLE public.fila_dlq ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Acesso total para service_role e anon" 
ON public.fila_dlq 
FOR ALL 
TO anon, authenticated, service_role
USING (true)
WITH CHECK (true);

COMMENT ON TABLE public.fila_dlq IS 'Fila de Dead Letter (DLQ) para capturar e reprocessar alvos com falhas consecutivas de coleta.';
