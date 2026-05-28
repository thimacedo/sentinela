'use client';

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase'; // Assuming standard setup, let's verify.

export function useWallet() {
  const [balance, setBalance] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchBalance = async () => {
    try {
      if (typeof window === 'undefined') return;
      
      const userId = localStorage.getItem('sentinela_user_id');
      
      // Fallback for demo/guest if no auth implemented yet, but we should fetch from Supabase if possible
      if (!userId) {
        setBalance(0);
        setLoading(false);
        return;
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
    // Optional: Set up real-time subscription here later if needed
  }, []);

  return { balance, loading, refreshBalance: fetchBalance };
}
