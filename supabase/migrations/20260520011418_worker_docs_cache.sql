CREATE TABLE worker_docs_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_key text UNIQUE NOT NULL,
  content text NOT NULL,
  fetched_at timestamptz DEFAULT now(),
  expires_at timestamptz NOT NULL
);