'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

const BETA_TESTER_ID = '79c43352-0c67-430a-9cf5-087c49367a6f';

export function useWallet() {
  const [balance, setBalance] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchBalance = async () => {
    try {
      if (typeof window === 'undefined') return;
      
      let userId = localStorage.getItem('sentinela_user_id');
      
      // Validação Simples (BETA): Atribui a conta de Teste de Estresse se não logado
      if (!userId || userId === 'guest') {
        userId = BETA_TESTER_ID;
        localStorage.setItem('sentinela_user_id', userId);
      }

      // Supabase query to 'profiles' table
      const { data, error } = await supabase
        .from('profiles')
        .select('stn_tokens')
        .eq('id', userId)
        .single();

      if (error) throw error;
      
      if (data) {
        setBalance(data.stn_tokens || 0);
      }
    } catch (error) {
      console.error('Erro ao buscar carteira:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Adia a execução para evitar cascading renders (PASA v60.1 compliance)
    const timeout = setTimeout(() => {
      fetchBalance();
    }, 0);
    
    return () => clearTimeout(timeout);
  }, []);

  return { balance, loading, refreshBalance: fetchBalance };
}
