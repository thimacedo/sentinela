-- 1. Tabela de Backoff (Controla Rate Limiting)
CREATE TABLE IF NOT EXISTS public.alvo_backoff (
    candidato_id text PRIMARY KEY,
    strikes int NOT NULL DEFAULT 0,
    next_allowed_at timestamptz NOT NULL
);

-- 2. Índices de performance para a fila
CREATE INDEX IF NOT EXISTS idx_alvo_backoff_next_allowed 
ON public.alvo_backoff (next_allowed_at);
