'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { supabase } from '@/src/lib/supabase';

interface SeriesData {
  hora: string;
  alertas: number;
}

export default function ActivityChart() {
  const { data = [], isLoading } = useQuery<SeriesData[]>({
    queryKey: ['temporal-series'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/v1/analytics/temporal-series');
        if (!response.ok) {
          throw new Error(`API respondeu com status ${response.status}`);
        }
        return await response.json();
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
          .eq('is_hate', true)
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
    <Card className="bg-black/50 border-tactical-accent mt-6">
      <CardHeader>
        <CardTitle className="text-tactical-accent text-sm uppercase tracking-wider flex justify-between items-center">
          Atividade de Alertas (48h)
          <span className="text-[10px] text-gray-500 font-mono">SENSOR DE PULSO ATIVO</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[300px] w-full pt-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-500 font-mono animate-pulse">
            VARRENDO ESPECTRO TEMPORAL...
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 font-mono italic">
            SEM PULSOS DETECTADOS NO PERÍODO.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorAlerts" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff41" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00ff41" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false} />
              <XAxis 
                dataKey="hora_formatada" 
                stroke="#333" 
                fontSize={10} 
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#333" 
                fontSize={10} 
                tickLine={false}
                axisLine={false}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#000', border: '1px solid #00ff41', borderRadius: '0', fontSize: '12px' }}
                itemStyle={{ color: '#00ff41' }}
                labelStyle={{ color: '#666', marginBottom: '4px' }}
              />
              <Area 
                type="monotone" 
                dataKey="alertas" 
                stroke="#00ff41" 
                fillOpacity={1} 
                fill="url(#colorAlerts)" 
                strokeWidth={2}
                animationDuration={1500}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
