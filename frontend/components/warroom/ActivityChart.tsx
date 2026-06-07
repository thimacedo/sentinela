'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { supabase } from '@/lib/supabase';
import { fetchApi } from '@/lib/api';

interface SeriesData {
  hora: string;
  alertas: number;
}

export default function ActivityChart() {
  const { data = [], isLoading } = useQuery<SeriesData[]>({
    queryKey: ['temporal-series'],
    queryFn: async () => {
      try {
        return await fetchApi('/api/v1/analytics/temporal-series');
      } catch (error) {
        console.warn("Erro ao buscar série temporal da API, tentando fallback Supabase:", error);
      }

      // Fallback Supabase
      try {
        const windowDate = new Date();
        windowDate.setHours(windowDate.getHours() - 48);
        const windowStr = windowDate.toISOString();

        const { data: comments, error } = await supabase
          .from('comentarios')
          .select('data_coleta')
          .in('categoria_ia', ['ODIO_IDENTITARIO', 'VIOLENCIA_GENERO', 'AMEACA'])
          .gte('data_coleta', windowStr)
          .order('data_coleta', { ascending: true });

        if (error || !comments) {
          console.error("Erro no fallback Supabase:", error);
          return [];
        }

        const hoursMap: Record<string, number> = {};
        comments.forEach((c: any) => {
          if (c.data_coleta) {
            const hourKey = c.data_coleta.slice(0, 13) + ":00:00";
            hoursMap[hourKey] = (hoursMap[hourKey] || 0) + 1;
          }
        });

        const series = Object.entries(hoursMap).map(([hora, alertas]) => ({
          hora,
          alertas,
        }));

        return series.sort((a, b) => a.hora.localeCompare(b.hora));
      } catch (err) {
        console.error("Erro crítico no fallback Supabase da série temporal:", err);
      }
      return [];
    },
    refetchInterval: 60000,
  });

  // Formata a hora para exibição (ex: 2026-05-18T14:00:00 -> 14h)
  const chartData = data.map(item => ({
    ...item,
    hora_formatada: new Date(item.hora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }));

  return (
    <Card className="bg-slate-900/50 border-slate-800 shadow-xl overflow-hidden">
      <CardHeader className="border-b border-slate-800/50 pb-4">
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-slate-100 text-lg font-bold tracking-tight">
              Análise Temporal <span className="text-emerald-500/50 font-normal ml-1">48h</span>
            </CardTitle>
            <p className="text-[10px] text-slate-500 font-mono uppercase mt-1 tracking-widest">
              Fluxo de Alertas Detectados
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-950 rounded-full border border-slate-800">
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-[9px] font-mono text-slate-400 font-bold uppercase tracking-tighter">Live Monitor</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="relative h-[350px] min-h-[350px] w-full pt-8 px-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-slate-600 animate-pulse font-mono text-xs">
            DESSERIALIZANDO SÉRIE TEMPORAL...
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-700 font-mono text-xs italic">
            NENHUM REGISTRO ENCONTRADO NO PERÍODO.
          </div>
        ) : (
          <div className="w-full h-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.5} />
              <XAxis 
                dataKey="hora_formatada" 
                stroke="#475569" 
                fontSize={9} 
                tickLine={false}
                axisLine={false}
                dy={10}
              />
              <YAxis 
                stroke="#475569" 
                fontSize={9} 
                tickLine={false}
                axisLine={false}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#0f172a', 
                  border: '1px solid #334155', 
                  borderRadius: '8px', 
                  fontSize: '11px',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                }}
                itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
                labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                cursor={{ stroke: '#334155', strokeWidth: 1 }}
              />
              <Area 
                type="monotone" 
                dataKey="alertas" 
                stroke="#10b981" 
                fillOpacity={1} 
                fill="url(#colorAlerts)" 
                strokeWidth={2}
                animationDuration={2000}
                activeDot={{ r: 4, strokeWidth: 0, fill: '#34d399' }}
              />
            </AreaChart>
          </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
