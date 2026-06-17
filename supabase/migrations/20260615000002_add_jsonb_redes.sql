ALTER TABLE candidatos
ADD COLUMN IF NOT EXISTS redes_sociais JSONB;

UPDATE candidatos
SET redes_sociais = jsonb_build_object(
  'bluesky', bsky_handle,
  'telegram', telegram_channel,
  'reddit_keywords', ARRAY[reddit_query]
);

ALTER TABLE candidatos
DROP COLUMN IF EXISTS bsky_handle,
DROP COLUMN IF EXISTS telegram_channel,
DROP COLUMN IF EXISTS reddit_query;
