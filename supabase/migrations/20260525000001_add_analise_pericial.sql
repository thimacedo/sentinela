-- Migration: Add analise_pericial to comentarios (v65.2)
-- Descrição: Adiciona coluna para análise pericial detalhada da IA e Bots.

ALTER TABLE public.comentarios 
ADD COLUMN IF NOT EXISTS analise_pericial TEXT;

-- Comentário para o PostgREST recarregar o schema
COMMENT ON COLUMN public.comentarios.analise_pericial IS 'Análise pericial detalhada gerada pela IA (MCA v2.2) ou Detecção de Bots.';

-- Recarregar cache do PostgREST
NOTIFY pgrst, 'reload schema';
