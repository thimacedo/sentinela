CREATE TABLE worker_suggestions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id text NOT NULL,
  cycle integer NOT NULL,
  suggestion text NOT NULL,
  status text DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'approved', 'rejected')),
  timestamp timestamptz DEFAULT now()
);