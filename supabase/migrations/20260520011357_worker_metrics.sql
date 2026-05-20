CREATE TABLE worker_metrics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id text NOT NULL,
  cycle integer NOT NULL,
  items_collected integer DEFAULT 0,
  items_failed integer DEFAULT 0,
  duration_seconds float,
  errors jsonb,
  timestamp timestamptz DEFAULT now()
);