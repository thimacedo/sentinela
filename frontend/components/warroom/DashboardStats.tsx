'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from '@/src/lib/supabase';

interface Stats {
  total_monitorados: number;
  total_alertas: number;
  total_amostra: number;
  resiliencia: number;
}

export default function WarRoom() {
  const [stats, setStats] = useState<Stats>({
    total_monitorados: 0,
    total_alertas: 0,
    total_amostra: 0,
    resiliencia: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        // Tenta buscar da API (se estiver rodando localmente ou no Vercel)
        const response = await fetch('/api/v1/summary');
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        } else {
          // Fallback direto via Supabase se a API falhar
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

          setStats({
            total_monitorados: monitorados || 0,
            total_alertas,
            total_amostra,
            resiliencia,
          });
        }
      } catch (error) {
        console.error("Erro ao buscar stats:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  const round = (num: number, precision: number) => {
    const factor = Math.pow(10, precision);
    return Math.round(num * factor) / factor;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Alvos Ativos</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">{loading ? "..." : stats.total_monitorados}</p>
        </CardContent>
      </Card>
      
      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Indícios Detectados</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">{loading ? "..." : stats.total_alertas.toLocaleString()}</p>
        </CardContent>
      </Card>

      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Volume Analisado</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold">{loading ? "..." : stats.total_amostra.toLocaleString()}</p>
        </CardContent>
      </Card>

      <Card className="bg-black/50 border-tactical-accent">
        <CardHeader>
          <CardTitle className="text-tactical-accent text-sm uppercase">Índice de Resiliência</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-4xl font-bold text-tactical-accent">{loading ? "..." : `${stats.resiliencia}%`}</p>
        </CardContent>
      </Card>
    </div>
  );
}
