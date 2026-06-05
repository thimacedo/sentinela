-- migrations/20260604_add_audit_data.sql
-- Adiciona suporte para persistência de dados de auditoria analítica no repositório de comentários.

ALTER TABLE comentarios 
ADD COLUMN IF NOT EXISTS audit_data JSONB;

-- Comentário para documentação do schema cache
COMMENT ON COLUMN comentarios.audit_data IS 'Armazena o JSON de reclassificação cruzada gerado pelo AuditAgent (Groq/Llama).';
