'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from '@/src/lib/supabase';

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
        const response = await fetch('/api/v1/summary');
        if (response.ok) {
          return await response.json();
        }
      } catch (error) {
        console.warn("API Summary falhou, tentando fallback Supabase:", error);
      }

      // Fallback Supabase
      const { count: monitorados } = await supabase
        .from('candidatos')
        .select('*', { count: 'exact', head: true })
        .eq('status_monitoramento', 'Ativo');

      const { data: candidates } = await supabase
        .from('candidatos')
        .select('comentarios_totais_count, comentarios_odio_count');

      const total_amostra = candidates?.reduce((acc, c) => acc + (c.comentarios_totais_count || 0), 0) || 0;
      const total_alertas = candidates?.reduce((acc, c) => acc + (c.comentarios_odio_count || 0), 0) || 0;
      const resiliencia = total_amostra > 0 ? round(((total_amostra - total_alertas) / total_amostra) * 100, 1) : 100.0;

      return {
        total_monitorados: monitorados || 0,
        total_alertas,
        total_amostra,
        resiliencia,
      };
    },
    refetchInterval: 30000, // Atualiza a cada 30 segundos
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
