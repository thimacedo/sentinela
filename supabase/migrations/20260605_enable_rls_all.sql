-- 🔐 SEGURANÇA E CONFORMIDADE (RLS) - SENTINELA v50.1
-- Habilita RLS e define políticas de acesso para todas as tabelas principais.

-- 1. Habilitar RLS em todas as tabelas (incluindo possíveis aliases e tabelas legadas)
DO $$ 
DECLARE 
    t text;
    tables_to_rls text[] := ARRAY[
        'candidatos', 'comentarios', 'fila_coleta', 'dossies', 
        'system_alerts', 'threat_alerts', 'profiles', 'ci_transactions', 
        'worker_rewards', 'worker_ledger', 'fallback_logs', 'worker_sessions', 
        'worker_metrics', 'worker_suggestions', 'lotes_analises', 
        'system_directives', 'worker_docs_cache', 'network_clusters', 
        'push_notifications', 'audit_logs', 'kpis'
    ];
BEGIN 
    FOREACH t IN ARRAY tables_to_rls LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = t) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
        END IF;
    END LOOP;
END $$;

-- 2. Limpeza de políticas existentes para garantir idempotência (v50.1)
DO $$ 
DECLARE 
    pol text;
    t text;
BEGIN 
    FOR t, pol IN (SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public') LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', pol, t);
    END LOOP;
END $$;

-- 3. Políticas para SERVICE_KEY (Backend / Workers)
-- Concedemos acesso total a todas as tabelas para a service_role.
DO $$ 
DECLARE 
    t text;
BEGIN 
    FOR t IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE format('CREATE POLICY "Service Role Full Access" ON public.%I FOR ALL TO service_role USING (true) WITH CHECK (true);', t);
    END LOOP;
END $$;

-- 4. Políticas para ANON_KEY (Frontend Público - Leitura)
-- Tabelas que o frontend pode ler livremente.
DO $$ 
DECLARE 
    t text;
    public_read_tables text[] := ARRAY[
        'candidatos', 'comentarios', 'dossies', 'kpis', 'worker_rewards', 
        'network_clusters', 'system_alerts', 'threat_alerts'
    ];
BEGIN 
    FOREACH t IN ARRAY public_read_tables LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = t) THEN
            EXECUTE format('CREATE POLICY "Public Read Access" ON public.%I FOR SELECT TO anon USING (true);', t);
            EXECUTE format('CREATE POLICY "Authenticated Read Access" ON public.%I FOR SELECT TO authenticated USING (true);', t);
        END IF;
    END LOOP;
END $$;

-- 5. Políticas Específicas para Usuários Autenticados (Profiles e Transações)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'profiles') THEN
        EXECUTE 'CREATE POLICY "Users can read own profile" ON public.profiles FOR SELECT TO authenticated USING (auth.uid() = id);';
        EXECUTE 'CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ci_transactions') THEN
        EXECUTE 'CREATE POLICY "Users can read own transactions" ON public.ci_transactions FOR SELECT TO authenticated USING (auth.uid() = de_profile_id OR auth.uid() = para_profile_id);';
    END IF;
END $$;

-- 6. Auditoria (Apenas leitura para Admin autenticado se houver claims de role)
-- Como o sistema usa service_role para o orquestrador, deixamos audit_logs protegida (apenas service_role).
-- Se houver necessidade de admin UI, adicionar políticas baseadas em claims de JWT aqui futuramente.
