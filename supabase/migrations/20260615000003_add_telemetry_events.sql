-- Migration: Adiciona Telemetria OODA & SRE
-- Description: Cria tabela genérica de eventos de telemetria jsonb com índices para consultas performáticas.

CREATE TABLE telemetry_events (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type      TEXT NOT NULL,        
    source_module   TEXT NOT NULL,        
    provider_name   TEXT,                 
    status          TEXT,                 
    candidato_id    TEXT,                 
    comment_id      TEXT,                 
    duration_ms     INTEGER,              
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,  
    organization_id TEXT                  
);

CREATE INDEX idx_telemetry_events_type_time ON telemetry_events (event_type, created_at DESC);
CREATE INDEX idx_telemetry_events_provider ON telemetry_events (provider_name, created_at DESC);
CREATE INDEX idx_telemetry_events_org ON telemetry_events (organization_id, created_at DESC);
