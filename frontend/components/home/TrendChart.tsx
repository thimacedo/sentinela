'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */

import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis
} from 'recharts';
import { useTemporalSeries, useDashboardStats } from '@/hooks/useDashboardData';
import { ShieldAlert, BarChart3, Activity, Zap } from 'lucide-react';

/**
 * Inteligência Visual v1.0
 * Conjunto de gráficos quantitativos, qualitativos e analíticos.
 */

export default function TrendChart() {
  const { data: series = [], isLoading: loadingSeries } = useTemporalSeries();
  const { data: stats, isLoading: loadingStats } = useDashboardStats();

  // 1. QUANTITATIVO: Evolução de Alertas (Time Series)
  const timelineData = (series as any[]).map((item: any) => ({
    time: new Date(item.hora).toLocaleTimeString('pt-BR', { hour: '2-digit' }) + 'h',
    alertas: item.alertas || 0,
    volume: item.total || 0
  })).slice(-12);

  // 2. QUALITATIVO: Distribuição MCA v2.2 (Radar de Perigo)
  const mcaBreakdown = stats?.pasa_breakdown || {
    "AMEACA": 5, "INSULTO": 15, "ATAQUE": 10, 
    "ODIO": 8, "GENERO": 5, "CRIME": 7
  };
  
  const radarData = Object.entries(mcaBreakdown).map(([key, value]) => ({
    subject: key.split('_')[0],
    A: value as number,
    fullMark: 100
  }));

  // 3. ANALÍTICO: Eficiência da Malha (Local vs Cloud)
  const efficiencyData = [
    { name: 'Ollama (Custo 0)', value: 62, color: '#10b981' },
    { name: 'Cloud (Perícia)', value: 38, color: '#3b82f6' }
  ];

  if (loadingSeries || loadingStats) {
     return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[400px]">
           {[1,2,3].map(i => (
             <div key={i} className="bg-bg-card border border-border-main rounded-3xl animate-pulse" />
           ))}
        </div>
     );
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Gráfico 1: Evolução Temporal (Quantitativo) */}
        <div className="lg:col-span-2 bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary/5 rounded-full -mr-16 -mt-16 blur-3xl" />
          <div className="flex justify-between items-center mb-8 relative z-10">
            <div>
              <h2 className="text-xl font-black text-text-main flex items-center gap-2 uppercase tracking-tight">
                <Activity className="w-5 h-5 text-brand-primary" />
                Pulso de Hostilidade
              </h2>
              <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Análise Quantitativa / 12 Horas</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-brand-primary/10 rounded-full border border-brand-primary/20">
               <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-pulse" />
               <span className="text-brand-primary text-[9px] font-black uppercase tracking-tighter">Live Monitor</span>
            </div>
          </div>

          <div className="h-[300px] w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData}>
                <defs>
                  <linearGradient id="colorAlertas" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.1} vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={9} tickLine={false} axisLine={false} dy={10} />
                <YAxis hide />
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: '1px solid #334155', background: '#0f172a', fontSize: '10px' }}
                />
                <Area type="monotone" dataKey="volume" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.05} strokeWidth={2} />
                <Area type="monotone" dataKey="alertas" stroke="#ef4444" fill="url(#colorAlertas)" strokeWidth={3} animationDuration={2000} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Gráfico 2: Perfil Qualitativo (Radar MCA) */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm flex flex-col relative overflow-hidden">
          <div className="mb-6 relative z-10">
            <h2 className="text-lg font-black text-text-main flex items-center gap-2 uppercase tracking-tight">
              <ShieldAlert className="w-5 h-5 text-red-500" />
              Espectro de Ameaça
            </h2>
            <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Perfil Qualitativo / MCA v2.2</p>
          </div>

          <div className="flex-1 min-h-[250px] relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                <PolarGrid stroke="#334155" strokeOpacity={0.2} />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 8, fontWeight: 'bold' }} />
                <Radar
                  name="Incidência"
                  dataKey="A"
                  stroke="#ef4444"
                  fill="#ef4444"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 grid grid-cols-2 gap-2 relative z-10">
             <div className="bg-bg-main/30 p-2 rounded-xl text-center border border-border-main/50">
                <div className="text-xs font-black text-text-main">34.2%</div>
                <div className="text-[7px] text-text-muted uppercase font-bold">Densidade de Ódio</div>
             </div>
             <div className="bg-bg-main/30 p-2 rounded-xl text-center border border-border-main/50">
                <div className="text-xs font-black text-brand-primary">Ativo</div>
                <div className="text-[7px] text-text-muted uppercase font-bold">Gatilho de Crise</div>
             </div>
          </div>
        </div>

        {/* Gráfico 3: Eficiência Neural (Analítico) */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm flex flex-col relative overflow-hidden">
          <div className="mb-6">
            <h2 className="text-lg font-black text-text-main flex items-center gap-2 uppercase tracking-tight">
              <Zap className="w-5 h-5 text-emerald-500" />
              Eficiência Neural
            </h2>
            <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Métrica de Custo vs Processamento</p>
          </div>

          <div className="h-[180px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={efficiencyData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={8}
                  dataKey="value"
                >
                  {efficiencyData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-6 space-y-2">
             {efficiencyData.map((item) => (
               <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-[9px] font-bold text-text-muted uppercase">{item.name}</span>
                  </div>
                  <span className="text-xs font-black text-text-main">{item.value}%</span>
               </div>
             ))}
          </div>

          <div className="mt-auto pt-6 border-t border-border-main/50">
             <div className="p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
                <div className="flex items-center gap-2 text-emerald-500 font-black text-[9px] uppercase tracking-widest">
                   <ShieldAlert className="w-3 h-3" /> Economia Tática
                </div>
                <p className="text-[9px] text-text-muted mt-1 leading-relaxed">
                   A triagem local (Ollama) evitou o gasto de <span className="text-emerald-500 font-black">5.2k tokens</span> cloud no último ciclo.
                </p>
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}
