-- Adiciona campo de governança para alvos
ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS identidade_validada BOOLEAN DEFAULT NULL;
ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS motivo_desativacao TEXT DEFAULT NULL;

-- Comentários para documentação do schema
COMMENT ON COLUMN candidatos.identidade_validada IS 'Define se o alvo foi validado pelo TargetResearchWorker como pertencente ao escopo do projeto.';
COMMENT ON COLUMN candidatos.motivo_desativacao IS 'Justificativa para a negativa de validação ou desativação do alvo.';
