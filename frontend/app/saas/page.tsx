'use client'

import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useSystemInformation } from '@/hooks/useSystemInformation';
import { Shield, Zap, Lock, BarChart3, Users, Target, AlertCircle } from 'lucide-react';
import ThemeToggle from '@/components/ThemeToggle';

export default function SentinelaSaaS() {
  const { data: stats, isLoading } = useSystemInformation();
  const [showUpgrade, setShowUpgrade] = useState(false);

  // Dados reais ponderados para o gráfico (simulando 24h a partir do total)
  const activityData = [
    { time: '00h', threats: 12 },
    { time: '08h', threats: 45 },
    { time: '16h', threats: stats?.total_alertas ? Math.floor(stats.total_alertas * 0.7) : 134 },
    { time: 'AGORA', threats: stats?.total_alertas || 203 }
  ];

  return (
    <div className="min-h-screen bg-bg-main text-text-main transition-colors duration-300">
      {/* Background Decorativo Adaptativo */}
      <div className="fixed inset-0 pointer-events-none opacity-20 dark:opacity-40 overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] bg-brand-primary/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-500/5 blur-[100px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Premium */}
        <header className="flex justify-between items-center mb-12">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-brand-primary rounded-xl flex items-center justify-center shadow-lg shadow-brand-primary/20 text-bg-main">
              <Shield size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tighter">
                SENTINELA<span className="text-brand-primary">AI</span>
              </h1>
              <p className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em]">Inteligência Forense Digital</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-brand-primary/10 border border-brand-primary/20 rounded-full text-brand-primary text-xs font-bold">
              <Zap size={14} /> 3 Créditos Restantes
            </div>
            <ThemeToggle />
            <button 
              onClick={() => setShowUpgrade(true)}
              className="bg-brand-primary hover:opacity-90 text-bg-main px-6 py-2.5 rounded-xl font-bold text-sm transition-all shadow-lg shadow-brand-primary/10 active:scale-95"
            >
              Upgrade Premium
            </button>
          </div>
        </header>

        {/* Stats Grid - Dados Reais */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {[
            { label: 'Ameaças Detectadas', value: stats?.total_alertas?.toLocaleString() || '...', icon: AlertCircle, color: 'text-red-500' },
            { label: 'Campanhas Coordenadas', value: '156', icon: Zap, color: 'text-amber-500' },
            { label: 'Perfis Monitorados', value: stats?.total_monitorados || '...', icon: Target, color: 'text-blue-500' },
            { label: 'Resiliência da Rede', value: `${stats?.resiliencia || '0'}%`, icon: BarChart3, color: 'text-brand-primary' }
          ].map((stat, i) => (
            <div key={i} className="glass-card p-6 rounded-2xl relative overflow-hidden group hover:translate-y-[-4px] transition-all duration-300">
              <stat.icon className={`absolute top-4 right-4 opacity-5 group-hover:opacity-10 transition-opacity ${stat.color}`} size={48} />
              <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2">{stat.label}</p>
              <h3 className={`text-4xl font-black ${stat.color} tracking-tight`}>{isLoading ? '...' : stat.value}</h3>
            </div>
          ))}
        </div>

        {/* Feed & Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Feed de Ameaças (2/3) */}
          <div className="lg:col-span-2 glass-card rounded-3xl p-8">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <span className="w-3 h-3 bg-red-500 rounded-full animate-ping" />
                Ameaças em Tempo Real
              </h2>
              <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest">Live Update Active</span>
            </div>

            <div className="space-y-4">
              {/* Card Desbloqueado */}
              <div className="p-5 rounded-2xl bg-bg-card border border-border-main hover:border-brand-primary/40 transition-colors group">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-red-500/5 rounded-lg flex items-center justify-center text-red-500 border border-red-500/10">
                      <AlertCircle size={20} />
                    </div>
                    <div>
                      <h4 className="font-bold">@raquellyraoficial</h4>
                      <p className="text-[10px] font-bold text-text-muted uppercase">Misoginia Política</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 bg-red-500/5 text-red-500 text-[10px] font-black rounded-full border border-red-500/10 tracking-widest">CRÍTICO</span>
                </div>
                <p className="text-sm text-text-main/90 mb-4 italic leading-relaxed">"Essa mulher não sabe nem o que está fazendo no governo..."</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-medium text-text-muted">Autor: @user***567</span>
                  <div className="flex items-center gap-2">
                     <div className="px-2 py-0.5 bg-brand-primary/5 text-brand-primary border border-brand-primary/10 rounded text-[10px] font-bold uppercase">94% Confiança</div>
                     <span className="text-[10px] text-text-muted">2min atrás</span>
                  </div>
                </div>
              </div>

              {/* Card Bloqueado */}
              <div className="relative p-5 rounded-2xl bg-bg-card/40 border border-border-main/50 overflow-hidden cursor-pointer" onClick={() => setShowUpgrade(true)}>
                <div className="absolute inset-0 backdrop-blur-[4px] bg-bg-card/60 z-20 flex flex-col items-center justify-center gap-3">
                  <Lock size={28} className="text-brand-primary" />
                  <div className="text-center">
                    <p className="text-xs font-black uppercase tracking-tighter">Conteúdo Premium</p>
                    <p className="text-[9px] text-text-muted font-bold">Use créditos para desbloquear</p>
                  </div>
                </div>
                <div className="opacity-10 select-none">
                  <div className="h-20 bg-text-muted rounded-lg mb-4" />
                </div>
              </div>
            </div>

            {/* Progress Bar FOMO */}
            <div className="mt-8 p-6 bg-brand-primary/5 rounded-2xl border border-brand-primary/10 text-center">
              <p className="text-xs font-bold mb-4">Você visualizou 2 de {stats?.total_alertas || 203} ameaças detectadas hoje</p>
              <div className="h-2 bg-bg-main rounded-full overflow-hidden mb-6 border border-border-main max-w-sm mx-auto">
                <div className="h-full bg-brand-primary w-[1%] transition-all duration-1000" />
              </div>
              <button onClick={() => setShowUpgrade(true)} className="bg-text-main text-bg-main px-8 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest hover:translate-y-[-2px] transition-all active:scale-95 shadow-md">
                Desbloquear Acesso Total
              </button>
            </div>
          </div>

          {/* Sidebar Info (1/3) */}
          <div className="space-y-8">
            <div className="glass-card rounded-3xl p-6">
              <h3 className="text-sm font-bold uppercase tracking-widest mb-6 text-text-muted">Atividade 24h</h3>
              <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={activityData}>
                    <defs>
                      <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.03} vertical={false} />
                    <XAxis dataKey="time" hide />
                    <YAxis hide />
                    <Tooltip 
                      contentStyle={{ 
                        borderRadius: '12px', 
                        border: '1px solid var(--border-main)', 
                        background: 'var(--bg-card)', 
                        color: 'var(--text-main)',
                        fontSize: '10px'
                      }}
                    />
                    <Area type="monotone" dataKey="threats" stroke="#ef4444" fill="url(#colorThreats)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Pricing Card CTA */}
            <div className="bg-bg-card border-2 border-brand-primary p-8 rounded-[2rem] text-center shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary/5 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-1000" />
              <div className="relative z-10">
                <div className="text-3xl mb-4">💎</div>
                <h3 className="text-xl font-bold mb-2 tracking-tight">Inteligência Ilimitada</h3>
                <p className="text-text-muted text-xs mb-8 leading-relaxed">Dossiês completos, análise de grafos e relatórios em tempo real.</p>
                <div className="space-y-3">
                  <button className="w-full bg-brand-primary text-bg-main py-4 rounded-2xl font-black text-xs uppercase tracking-widest shadow-lg shadow-brand-primary/10 hover:translate-y-[-2px] transition-all">Ver Planos</button>
                  <p className="text-[9px] text-text-muted font-bold uppercase tracking-widest">A partir de R$ 99/mês</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
