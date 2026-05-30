'use client';

import React, { useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Sector
} from 'recharts';
import { useDemographics } from '@/hooks/useDashboardData';
import { Users, Filter, BarChart3, AlertTriangle, Sparkles, MapPin } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

// Custom Tooltip com design premium
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-bg-card border border-border-main p-4 rounded-2xl shadow-2xl backdrop-blur-xl">
        <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2">{label || payload[0].payload.name}</p>
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: payload[0].color || payload[0].payload.fill }} />
          <p className="text-xl font-black text-text-main tabular-nums leading-none">
            {payload[0].value} <span className="text-[10px] text-text-muted font-normal uppercase">ocorrências</span>
          </p>
        </div>
      </div>
    );
  }
  return null;
};

// Shape customizado para o PieChart (Donut com Hover Effect)
const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, value } = props;
  return (
    <g>
      <text x={cx} y={cy - 12} dy={8} textAnchor="middle" fill={fill} className="font-bold uppercase tracking-widest" style={{ fontSize: '10px' }}>
        {payload.name}
      </text>
      <text x={cx} y={cy + 12} dy={8} textAnchor="middle" fill="#94a3b8" className="font-black tabular-nums" style={{ fontSize: '18px' }}>
        {value}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        className="transition-all duration-300 drop-shadow-md"
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 10}
        outerRadius={outerRadius + 14}
        fill={fill}
        opacity={0.2}
      />
    </g>
  );
};

export default function DemographicsPage() {
  const { data, isLoading } = useDemographics();
  const [activeIndex, setActiveIndex] = useState(0);

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8 py-6">
        <div className="text-center py-32 flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-brand-primary/30 border-t-brand-primary rounded-full animate-spin" />
          <div className="text-text-muted animate-pulse font-mono text-[10px] uppercase tracking-widest">
            Sintetizando inteligência demográfica...
          </div>
        </div>
      </div>
    );
  }

  const { sexo = [], partido = [], estado = [], ideologia = [], top_alvos = [] } = data || {};

  // VIP Targets logic: highlight the most attacked
  const vipTargets = top_alvos.slice(0, 3);
  const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e'];

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6 px-4 sm:px-0">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-black text-text-main tracking-tight uppercase flex items-center gap-3">
            <div className="p-2 bg-brand-primary/10 rounded-xl">
              <Users className="w-6 h-6 text-brand-primary" />
            </div>
            Demografia de Ameaças
          </h1>
          <p className="text-xs text-text-muted mt-2 font-medium">
            Análise estrutural dos alvos mais atacados por gênero, ideologia, estado e partido político.
          </p>
        </div>
      </div>

      {/* VIP Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {vipTargets.map((vip: any, idx: number) => (
          <div key={vip.name} className="bg-bg-card border border-border-main rounded-3xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1 relative overflow-hidden group cursor-default glass-card">
             <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full -mr-16 -mt-16 blur-2xl group-hover:bg-red-500/10 transition-colors" />
             <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-red-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
             
             <div className="flex items-center gap-4 relative z-10 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-bg-main border border-border-main flex items-center justify-center font-black text-text-main shadow-inner text-lg">
                  {idx + 1}
                </div>
                <div>
                  <div className="text-[9px] font-bold text-red-500 uppercase tracking-widest flex items-center gap-1.5 mb-0.5">
                    <AlertTriangle className="w-3 h-3" /> Alvo Crítico
                  </div>
                  <div className="font-black text-text-main text-xl tracking-tight">@{vip.name}</div>
                </div>
             </div>
             <div className="flex items-end justify-between relative z-10 mt-4">
               <div className="text-4xl font-black text-text-main tabular-nums tracking-tighter">{vip.value}</div>
               <div className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1.5 bg-bg-main px-2 py-1 rounded-md border border-border-main/50">Validado</div>
             </div>
          </div>
        ))}
      </div>

      {/* AdSense In-feed */}
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
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-500/10 rounded-xl">
                <Filter className="w-5 h-5 text-indigo-500" />
              </div>
              <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Polarização Ideológica</h2>
            </div>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  activeIndex={activeIndex}
                  activeShape={renderActiveShape}
                  data={ideologia}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={95}
                  paddingAngle={5}
                  dataKey="value"
                  onMouseEnter={onPieEnter}
                  stroke="none"
                >
                  {ideologia.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} className="cursor-pointer hover:opacity-80 transition-opacity" />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-x-6 gap-y-3 mt-2">
             {ideologia.map((entry: any, index: number) => (
               <div key={entry.name} className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-main border border-border-main/50 hover:border-border-main transition-colors cursor-default">
                 <div className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                 <span className="text-[10px] font-bold text-text-main uppercase tracking-wider">{entry.name} <span className="text-text-muted ml-1">({entry.value})</span></span>
               </div>
             ))}
          </div>
        </div>

        {/* Gender Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center gap-3">
            <div className="p-2 bg-pink-500/10 rounded-xl">
              <Filter className="w-5 h-5 text-pink-500" />
            </div>
            <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Distribuição por Gênero</h2>
          </div>
          <div className="h-[280px] w-full mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sexo} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                <defs>
                  <linearGradient id="colorGender0" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ec4899" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ec4899" stopOpacity={0.2}/>
                  </linearGradient>
                  <linearGradient id="colorGender1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.2}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.1} vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={10} fontWeight="bold" />
                <YAxis hide />
                <Tooltip cursor={{ fill: '#334155', opacity: 0.05 }} content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={50} animationDuration={1500}>
                  {sexo.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={`url(#colorGender${index % 2})`} stroke={index === 0 ? '#ec4899' : '#3b82f6'} strokeWidth={1} />
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
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-xl">
              <BarChart3 className="w-5 h-5 text-blue-500" />
            </div>
            <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Pressão por Partido</h2>
          </div>
          <div className="h-[320px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={partido} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorParty" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.1} horizontal={false} />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} width={80} fontWeight="bold" />
                <Tooltip cursor={{ fill: '#334155', opacity: 0.05 }} content={<CustomTooltip />} />
                <Bar dataKey="value" fill="url(#colorParty)" radius={[0, 6, 6, 0]} barSize={20} animationDuration={1500}>
                  {partido.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill="url(#colorParty)" className="hover:opacity-80 transition-opacity" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* State Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-xl">
              <MapPin className="w-5 h-5 text-emerald-500" />
            </div>
            <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Mapeamento Estadual</h2>
          </div>
          <div className="h-[320px] w-full mt-4">
            {estado && estado.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={estado} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorState" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.8}/>
                      <stop offset="100%" stopColor="#059669" stopOpacity={0.8}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.1} horizontal={false} />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} width={50} fontWeight="bold" />
                  <Tooltip cursor={{ fill: '#334155', opacity: 0.05 }} content={<CustomTooltip />} />
                  <Bar dataKey="value" fill="url(#colorState)" radius={[0, 6, 6, 0]} barSize={20} animationDuration={1500}>
                    {estado.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill="url(#colorState)" className="hover:opacity-80 transition-opacity" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center border-2 border-dashed border-border-main/50 rounded-2xl">
                <MapPin className="w-8 h-8 text-text-muted/30 mb-2" />
                <p className="text-xs text-text-muted font-bold uppercase tracking-widest">Aguardando dados geográficos</p>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* AdSense Multiplex (Bottom of page) */}
      <div className="mt-12 bg-bg-card/50 p-8 rounded-3xl border border-border-main glass-card relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-brand-primary/50 to-transparent opacity-50" />
        <div className="flex items-center gap-2 text-text-main font-bold text-[10px] uppercase tracking-widest mb-6 bg-bg-main w-fit px-3 py-1.5 rounded-md border border-border-main/50">
          <Sparkles className="w-4 h-4 text-brand-primary" /> Recomendações e Publicidade Integrada
        </div>
        <AdSenseSlot 
          adSlot="8564004420" 
          format="autorelaxed" 
        />
      </div>

    </div>
  );
}

