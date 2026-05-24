'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from '@/lib/supabase';
import { fetchApi } from '@/lib/api';

interface Stats {
  total_monitorados: number;
  total_alertas: number;
  total_amostra: number;
  resiliencia: number;
}

const round = (num: number, precision: number) => {
  const factor = Math.pow(10, precision);
  return Math.round(num * factor) / factor;
};

export default function DashboardStats() {
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
        return await fetchApi('/api/v1/summary');
      } catch (error) {
        console.warn("API Summary falhou, tentando fallback Supabase:", error);
      }

      // Fallback Supabase
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
        console.error("Erro crítico no fallback Supabase:", err);
        throw err;
      }
    },
    refetchInterval: 30000,
  });

  const displayStats = stats || {
    total_monitorados: 0,
    total_alertas: 0,
    total_amostra: 0,
    resiliencia: 0,
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Alvos Ativos</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">{isLoading ? "..." : displayStats.total_monitorados}</p>
        </CardContent>
      </Card>
      
      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Indícios Detectados</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">{isLoading ? "..." : displayStats.total_alertas.toLocaleString()}</p>
        </CardContent>
      </Card>

      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Volume Analisado</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">{isLoading ? "..." : displayStats.total_amostra.toLocaleString()}</p>
        </CardContent>
      </Card>

      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Índice de Resiliência</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold text-tactical-accent">{isLoading ? "..." : `${displayStats.resiliencia}%`}</p>
        </CardContent>
      </Card>
    </div>
  );
}
