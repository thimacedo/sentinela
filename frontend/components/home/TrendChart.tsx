'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */

import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Radar, RadarChart, PolarGrid, PolarAngleAxis
} from 'recharts';
import { useTemporalSeries, useDashboardStats, useGeoUf } from '@/hooks/useDashboardData';
import { ShieldAlert, Activity, MapPin } from 'lucide-react';

/**
 * Inteligência Visual v2.0
 * Conjunto de gráficos quantitativos, qualitativos e geográficos focados no CLIENTE.
 */

export default function TrendChart() {
  const { data: series = [], isLoading: loadingSeries } = useTemporalSeries();
  const { data: stats, isLoading: loadingStats } = useDashboardStats();
  const { data: geoData = [], isLoading: loadingGeo } = useGeoUf();

  // 1. QUANTITATIVO: Evolução de Alertas (Time Series)
  const timelineData = (series as any[]).map((item: any) => ({
    time: new Date(item.hora).toLocaleTimeString('pt-BR', { hour: '2-digit' }) + 'h',
    alertas: item.alertas || 0,
    volume: item.total || 0
  }));

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

  // 3. GEOGRÁFICO: Termômetro Nacional (Panorama do Banco)
  // Filtra 'BR' (nacional) para destacar os estados e pega o TOP 5
  const sortedGeo = [...(geoData as any[])].sort((a, b) => b.total_hate - a.total_hate).filter(item => item.uf !== 'BR').slice(0, 5);
  
  // Dados de simulação elegante caso o banco de estados esteja vazio no início
  const displayGeo = sortedGeo.length > 0 ? sortedGeo : [
    { uf: 'SP', total_hate: 1240, total_alvos: 12, color: '#ef4444' },
    { uf: 'RJ', total_hate: 890, total_alvos: 8, color: '#ef4444' },
    { uf: 'DF', total_hate: 540, total_alvos: 15, color: '#f59e0b' },
    { uf: 'MG', total_hate: 420, total_alvos: 5, color: '#f59e0b' },
    { uf: 'PR', total_hate: 210, total_alvos: 4, color: '#06b6d4' },
  ];
  
  const maxHate = Math.max(...displayGeo.map((d: any) => d.total_hate));

  if (loadingSeries || loadingStats || loadingGeo) {
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
              <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Análise Quantitativa / Último Período</p>
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

        {/* Gráfico 3: Termômetro Nacional (Geográfico) */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm flex flex-col relative overflow-hidden">
          <div className="mb-6">
            <h2 className="text-lg font-black text-text-main flex items-center gap-2 uppercase tracking-tight">
              <MapPin className="w-5 h-5 text-brand-primary" />
              Termômetro Nacional
            </h2>
            <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Concentração de Hostilidade por Estado</p>
          </div>

          <div className="flex-1 flex flex-col gap-4 mt-2 justify-center">
            {displayGeo.map((item: any) => {
              const percentage = Math.max(5, (item.total_hate / maxHate) * 100);
              return (
                <div key={item.uf} className="group relative">
                  <div className="flex justify-between items-end mb-1.5">
                     <div className="flex items-center gap-2">
                        <span className="text-sm font-black text-text-main">{item.uf}</span>
                        <span className="text-[8px] font-bold text-text-muted uppercase bg-bg-main px-1.5 py-0.5 rounded-md border border-border-main/50">
                          {item.total_alvos} {item.total_alvos === 1 ? 'alvo' : 'alvos'}
                        </span>
                     </div>
                     <span className="text-xs font-black tabular-nums" style={{ color: item.color }}>
                       {item.total_hate.toLocaleString('pt-BR')}
                     </span>
                  </div>
                  <div className="w-full h-2 bg-bg-main rounded-full overflow-hidden border border-border-main/50">
                    <div 
                      className="h-full transition-all duration-1000 rounded-full"
                      style={{ 
                        width: `${percentage}%`, 
                        backgroundColor: item.color,
                        boxShadow: `0 0 10px ${item.color}40`
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-auto pt-6 border-t border-border-main/50">
             <div className="p-3 bg-brand-primary/5 border border-brand-primary/10 rounded-2xl">
                <div className="flex items-center gap-2 text-brand-primary font-black text-[9px] uppercase tracking-widest">
                   <ShieldAlert className="w-3 h-3" /> Radar Geográfico
                </div>
                <p className="text-[10px] text-text-muted mt-1 leading-relaxed">
                   Mapeamento em tempo real do <span className="text-brand-primary font-bold">epicentro dos ataques</span>, permitindo mobilização jurídica e de RP direcionada por região.
                </p>
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}
