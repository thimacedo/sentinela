'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */

import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTemporalSeries } from '@/hooks/useDashboardData';

export default function TrendChart() {
  const { data = [], isLoading } = useTemporalSeries();

  // Formata os dados para o gráfico (v70.5)
  const chartData = (data as any[]).map((item: any) => ({
    time: new Date(item.hora).toLocaleTimeString('pt-BR', { hour: '2-digit' }) + 'h',
    threats: item.alertas || 0
  })).slice(-24); // Mostra as últimas 24 entradas

  return (
    <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold text-text-main flex items-center gap-3">
          <span className="w-3 h-3 bg-red-500 rounded-full animate-ping" />
          Atividade de Hostilidade (24h)
        </h2>
        <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest">Monitoramento Live Ativo</span>
      </div>

      <div className="h-[250px] w-full">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-text-muted font-mono text-xs animate-pulse">
            DESSERIALIZANDO SÉRIE TEMPORAL...
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center h-full text-text-muted font-mono text-xs italic">
            DADOS INSUFICIENTES PARA PLOTAGEM TEMPORAL.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.05} vertical={false} />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis hide />
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '12px', 
                  border: '1px solid var(--border-main)', 
                  background: 'var(--bg-card)', 
                  color: 'var(--text-main)',
                  fontSize: '11px',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
                }}
                itemStyle={{ color: '#ef4444', fontWeight: 'bold' }}
              />
              <Area 
                type="monotone" 
                dataKey="threats" 
                stroke="#ef4444" 
                fill="url(#colorThreats)" 
                strokeWidth={3}
                animationDuration={1500}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
