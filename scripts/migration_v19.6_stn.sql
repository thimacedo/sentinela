-- ==========================================
-- SENTINELA v19.6.0 - SCHEMA MUNIÇÃO FORENSE (COM PROFILES)
-- ==========================================

-- 1. Criar a tabela profiles (se não existir)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  avatar_url TEXT,
  stn_tokens INT DEFAULT 0,      -- Munição Forense
  total_stn_spent INT DEFAULT 0, -- Histórico de consumo
  updated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar RLS para Profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Usuário só pode ver e editar o próprio perfil
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- 2. Gatilho Mágico: Cria perfil automaticamente quando um usuário se registra no Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$ BEGIN
  INSERT INTO public.profiles (id, full_name, avatar_url)
  VALUES (
    new.id, 
    new.raw_user_meta_data->>'full_name', 
    new.raw_user_meta_data->>'avatar_url'
  );
  RETURN new;
END;
 $$ LANGUAGE plpgsql SECURITY DEFINER;

-- Conecta o gatilho ao cadastro
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 3. Criar tabela de Histórico de Transações (STN)
CREATE TABLE IF NOT EXISTS stn_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('PURCHASE', 'CONSUMPTION', 'BONUS')),
    amount INT NOT NULL, -- Positivo para recarga, Negativo para consumo
    stripe_session_id TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Habilitar RLS para Transações
ALTER TABLE stn_transactions ENABLE ROW LEVEL SECURITY;

-- Usuário só pode ver suas próprias transações
DROP POLICY IF EXISTS "Users can view own transactions" ON stn_transactions;
CREATE POLICY "Users can view own transactions" 
ON stn_transactions FOR SELECT 
USING (auth.uid() = user_id);

-- 4. Criar RPC Atômica (À prova de saldos negativos)
CREATE OR REPLACE FUNCTION process_stn_transaction(
    p_user_id UUID,
    p_amount INT,
    p_type TEXT,
    p_session_id TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$ DECLARE
    v_current_balance INT;
BEGIN
    -- Bloqueia consumo se o saldo for insuficiente
    IF p_amount < 0 THEN
        SELECT stn_tokens INTO v_current_balance FROM profiles WHERE id = p_user_id FOR UPDATE;
        IF v_current_balance < ABS(p_amount) THEN
            RAISE EXCEPTION 'INSUFFICIENT_FUNDS: Tentativa de fraude ou saldo insuficiente (Atual: %, Tentativa: %)', v_current_balance, ABS(p_amount);
        END IF;
    END IF;

    -- Atualiza o saldo na tabela de perfis
    UPDATE profiles 
    SET 
        stn_tokens = stn_tokens + p_amount,
        total_stn_spent = CASE WHEN p_amount < 0 THEN total_stn_spent + ABS(p_amount) ELSE total_stn_spent END,
        updated_at = now()
    WHERE id = p_user_id;

    -- Registra a transação no histórico
    INSERT INTO stn_transactions (user_id, type, amount, stripe_session_id, metadata)
    VALUES (p_user_id, p_type, p_amount, p_session_id, p_metadata);

    RETURN TRUE;
END;
 $$ LANGUAGE plpgsql SECURITY DEFINER;
