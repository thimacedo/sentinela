ALTER TABLE public.worker_suggestions DROP CONSTRAINT IF EXISTS worker_suggestions_status_check;
ALTER TABLE public.worker_suggestions ADD CONSTRAINT worker_suggestions_status_check 
  CHECK (status = ANY (ARRAY['pending_review'::text, 'approved'::text, 'rejected'::text, 'requires_human'::text, 'auto_applied'::text]));
