BEGIN;

-- 1) Schema + extensão
CREATE SCHEMA IF NOT EXISTS pgmq;
CREATE EXTENSION IF NOT EXISTS pgmq WITH SCHEMA pgmq;

-- 2) Filas necessárias
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE n.nspname='pgmq' AND c.relname='q_classify_comments') THEN
    PERFORM pgmq.create('classify_comments');
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE n.nspname='pgmq' AND c.relname='q_alerts') THEN
    PERFORM pgmq.create('alerts');
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                 WHERE n.nspname='pgmq' AND c.relname='q_cleanup') THEN
    PERFORM pgmq.create('cleanup');
  END IF;
END $$;

COMMIT;

-- 3) Recarregar PostgREST
SELECT pg_notify('pgrst', 'reload schema');
