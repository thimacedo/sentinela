'use client';

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { fetchApi } from '@/lib/api';

interface SystemStats {
  total_monitorados: number;
  total_alertas: number;
  total_amostra: number;
  resiliencia: number;
}

const round = (num: number, precision: number) => {
  const factor = Math.pow(10, precision);
  return Math.round(num * factor) / factor;
};

/**
 * Hook modular responsável por centralizar a inteligência de dados do sistema.
 * Segrega a lógica de busca (API/Supabase) da camada de visualização.
 */
export function useSystemInformation() {
  return useQuery<SystemStats>({
    queryKey: ['system-information'],
    queryFn: async () => {
      try {
        return await fetchApi('/api/v1/summary');
      } catch (error) {
        console.warn("API Summary falhou, tentando fallback Supabase:", error);
      }

      // Fallback Supabase (Inteligência Modular)
      try {
        const { count: monitorados } = await supabase
          .from('candidatos')
          .select('id', { count: 'exact', head: true })
          .eq('status_monitoramento', 'Ativo');

        const { count: total_amostra } = await supabase
          .from('comentarios')
          .select('id', { count: 'exact', head: true });

        const { count: total_alertas } = await supabase
          .from('comentarios')
          .select('id', { count: 'exact', head: true })
          .eq('is_hate', true);

        const resiliencia = (total_amostra && total_amostra > 0)
          ? round(((total_amostra - (total_alertas || 0)) / total_amostra) * 100, 1)
          : 100.0;

        return {
          total_monitorados: monitorados || 0,
          total_alertas: total_alertas || 0,
          total_amostra: total_amostra || 0,
          resiliencia,
        };
      } catch (err) {
        console.error("Erro crítico no provedor de informações:", err);
        throw err;
      }
    },
    refetchInterval: 30000,
  });
}
