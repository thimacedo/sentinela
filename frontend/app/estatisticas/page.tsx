'use client';

import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie
} from 'recharts';
import { useDemographics } from '@/hooks/useDashboardData';
import { Users, Filter, BarChart3, AlertTriangle, Sparkles } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export default function DemographicsPage() {
  const { data, isLoading } = useDemographics();

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8 py-6">
        <div className="text-center py-32 text-text-muted animate-pulse font-mono text-[10px] uppercase">
          Coletando dados demográficos do repositório...
        </div>
      </div>
    );
  }

  const { sexo = [], partido = [], estado = [], ideologia = [], top_alvos = [] } = data || {};

  // VIP Targets logic: highlight the most attacked
  const vipTargets = top_alvos.slice(0, 3);
  const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899'];

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase flex items-center gap-2">
            <Users className="w-6 h-6 text-brand-primary" />
            Demografia de Ameaças
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Análise estrutural dos alvos mais atacados por gênero, ideologia, estado e partido político.
          </p>
        </div>
      </div>

      {/* VIP Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {vipTargets.map((vip: any, idx: number) => (
          <div key={vip.name} className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm relative overflow-hidden group">
             <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full -mr-12 -mt-12 blur-2xl group-hover:bg-red-500/10 transition-colors" />
             <div className="flex items-center gap-3 relative z-10 mb-4">
                <div className="w-12 h-12 rounded-full bg-bg-main border border-border-main flex items-center justify-center font-black text-text-main shadow-inner text-lg">
                  {idx + 1}
                </div>
                <div>
                  <div className="text-[10px] font-bold text-red-500 uppercase tracking-widest flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Alvo Crítico
                  </div>
                  <div className="font-black text-text-main text-lg tracking-tight">@{vip.name}</div>
                </div>
             </div>
             <div className="flex items-end justify-between relative z-10 mt-6">
               <div className="text-3xl font-black text-text-main tabular-nums">{vip.value}</div>
               <div className="text-[9px] text-text-muted font-bold uppercase tracking-wider mb-1">Ataques Validados</div>
             </div>
          </div>
        ))}
      </div>

      {/* AdSense In-feed (Multiplex style but using native settings) */}
      <div className="my-8">
        <AdSenseSlot 
          adSlot="2190167769" 
          format="fluid" 
          layoutKey="-en+7+28-5k+1k" 
          style={{ textAlign: 'center' }} 
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Ideologia Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm">
          <div className="mb-6 flex items-center gap-2">
            <Filter className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Polarização Ideológica</h2>
          </div>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={ideologia}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {ideologia.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '16px', border: '1px solid #334155', background: '#0f172a', fontSize: '10px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 mt-4">
             {ideologia.map((entry: any, index: number) => (
               <div key={entry.name} className="flex items-center gap-2">
                 <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                 <span className="text-[10px] font-bold text-text-muted uppercase">{entry.name} ({entry.value})</span>
               </div>
             ))}
          </div>
        </div>

        {/* Gender Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm">
          <div className="mb-6 flex items-center gap-2">
            <Filter className="w-5 h-5 text-ec-400 text-pink-500" />
            <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Distribuição por Gênero</h2>
          </div>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sexo} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.1} vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis hide />
                <Tooltip 
                  cursor={{ fill: '#334155', opacity: 0.1 }}
                  contentStyle={{ borderRadius: '16px', border: '1px solid #334155', background: '#0f172a', fontSize: '10px' }}
                />
                <Bar dataKey="value" fill="#ec4899" radius={[4, 4, 0, 0]} barSize={40}>
                  {sexo.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#ec4899' : '#3b82f6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AdSense In-article */}
        <div className="lg:col-span-2">
          <AdSenseSlot 
            adSlot="1779104226" 
            format="fluid" 
            layout="in-article" 
            style={{ textAlign: 'center' }} 
          />
        </div>

        {/* Party Chart */}
        <div className="lg:col-span-2 bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm">
          <div className="mb-6 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-primary" />
            <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Pressão por Partido Político</h2>
          </div>
          <div className="h-[300px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={partido} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.1} horizontal={false} />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} width={80} />
                <Tooltip 
                  cursor={{ fill: '#334155', opacity: 0.1 }}
                  contentStyle={{ borderRadius: '16px', border: '1px solid #334155', background: '#0f172a', fontSize: '10px' }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24}>
                  {partido.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* AdSense Multiplex (Bottom of page) */}
      <div className="mt-12 bg-bg-main/30 p-6 rounded-3xl border border-border-main">
        <div className="flex items-center gap-2 text-text-muted font-bold text-[10px] uppercase tracking-widest mb-4">
          <Sparkles className="w-3 h-3" /> Recomendações e Publicidade Integrada
        </div>
        <AdSenseSlot 
          adSlot="8564004420" 
          format="autorelaxed" 
        />
      </div>

    </div>
  );
}
