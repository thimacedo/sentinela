-- migrations/20260605_fase2_otimizacao_subagentes.sql

-- 1. Cria a tabela de orquestração de lotes analíticos se não existir
CREATE TABLE IF NOT EXISTS public.lotes_analises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'PROCESSANDO', 'CONCLUIDO', 'ERRO')),
    processado_por TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- Habilita RLS na tabela por segurança
ALTER TABLE public.lotes_analises ENABLE ROW LEVEL SECURITY;

-- Permite acesso de leitura/escrita para service_role
CREATE POLICY "Permitir tudo para service_role" ON public.lotes_analises
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 2. Cria a function de claim atômico com SKIP LOCKED
CREATE OR REPLACE FUNCTION public.reivindicar_lote_analise(worker_name TEXT)
RETURNS TABLE (id UUID, batch_id UUID) AS $$
DECLARE
    lote_id UUID;
    lote_batch UUID;
BEGIN
    -- Busca e trava a primeira linha livre com SKIP LOCKED
    SELECT la.id, la.batch_id INTO lote_id, lote_batch
    FROM public.lotes_analises la
    WHERE la.status = 'PENDENTE'
    ORDER BY la.created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    -- Se encontrou, atualiza o status para PROCESSANDO e vincula o worker
    IF lote_id IS NOT NULL THEN
        UPDATE public.lotes_analises
        SET status = 'PROCESSANDO',
            processado_por = worker_name,
            updated_at = timezone('utc', now())
        WHERE public.lotes_analises.id = lote_id;
        
        RETURN QUERY SELECT la.id, la.batch_id FROM public.lotes_analises la WHERE la.id = lote_id;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
