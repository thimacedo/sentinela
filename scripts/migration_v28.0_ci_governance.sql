-- =======================================================
-- Migration v28.0 - Governança Financeira e Gestão de CI
-- Objetivo: Transição semântica de STN para CI e suporte atômico
-- =======================================================

-- 1. Renomear a coluna em profiles
ALTER TABLE public.profiles RENAME COLUMN stn_tokens TO saldo_ci;

-- 2. Renomear a tabela de transações
ALTER TABLE public.stn_transactions RENAME TO ci_transactions;

-- 3. Excluir a função atômica legada
DROP FUNCTION IF EXISTS process_stn_transaction;

-- 4. Criar a nova função atômica (com suporte a lock transacional)
CREATE OR REPLACE FUNCTION process_ci_transaction(
  p_user_id UUID,
  p_amount INT,
  p_type VARCHAR,
  p_description VARCHAR
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_current_balance INT;
  v_new_balance INT;
  v_transaction_id UUID;
BEGIN
  -- Bloqueio preventivo da linha para concorrência
  SELECT saldo_ci INTO v_current_balance
  FROM public.profiles
  WHERE id = p_user_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('success', false, 'message', 'Usuário não encontrado');
  END IF;

  -- Barreira anti-negativação para CONSUMPTION
  IF p_amount < 0 AND (v_current_balance + p_amount < 0) THEN
    RETURN jsonb_build_object('success', false, 'message', 'Saldo de CIs insuficiente para a operação');
  END IF;

  -- Efetiva o saque/depósito
  v_new_balance := v_current_balance + p_amount;
  
  UPDATE public.profiles
  SET saldo_ci = v_new_balance,
      updated_at = NOW()
  WHERE id = p_user_id;

  -- Gera o comprovante atômico da transação no ledger
  INSERT INTO public.ci_transactions (user_id, amount, type, description, created_at)
  VALUES (p_user_id, p_amount, p_type, p_description, NOW())
  RETURNING id INTO v_transaction_id;

  RETURN jsonb_build_object(
    'success', true, 
    'transaction_id', v_transaction_id,
    'new_balance', v_new_balance
  );
END;
$$;
