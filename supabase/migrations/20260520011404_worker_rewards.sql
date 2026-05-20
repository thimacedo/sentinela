CREATE TABLE worker_rewards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id text NOT NULL,
  cycle integer NOT NULL,
  score float NOT NULL,
  delta float,
  tier text,
  badges jsonb,
  recommendation text,
  timestamp timestamptz DEFAULT now()
);