-- Migration: Add analise_linguistica to comentarios (v98.6)
-- Descrição: Adiciona coluna JSONB para armazenar metadados linguísticos (lemmas, POS tags, dependências).

ALTER TABLE public.comentarios 
ADD COLUMN IF NOT EXISTS analise_linguistica JSONB;

-- Comentário para o PostgREST recarregar o schema
COMMENT ON COLUMN public.comentarios.analise_linguistica IS 'Metadados de análise linguística estruturada (lemmas, POS tags, dependências) gerados pelo Stanza.';

-- Recarregar cache do PostgREST
NOTIFY pgrst, 'reload schema';
