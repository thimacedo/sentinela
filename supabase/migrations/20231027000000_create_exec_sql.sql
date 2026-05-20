-- Função para permitir execução dinâmica de SQL (apenas para uso interno da Edge Function)
CREATE OR REPLACE FUNCTION exec_sql(query text)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE result json;
BEGIN
  EXECUTE 'SELECT json_agg(t) FROM (' || query || ') t' INTO result;
  RETURN result;
END;
$$;
