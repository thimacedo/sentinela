'use client';

import { TrendingUp, AlertTriangle, Users, Shield } from 'lucide-react';
import { useDashboardStats } from '@/hooks/useDashboardData';

interface NewsHeaderProps {
  todayHighlight?: {
    title: string;
    description: string;
    severity: 'critical' | 'high' | 'medium';
  };
}

export default function NewsHeader({ todayHighlight }: NewsHeaderProps) {
  const { data: stats, isLoading, error } = useDashboardStats();

  const severityColor = {
    critical: 'bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-400',
    high: 'bg-orange-500/10 border-orange-500/20 text-orange-600 dark:text-orange-400',
    medium: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-600 dark:text-yellow-400',
  };

  const severityIcon = {
    critical: '🚨',
    high: '⚠️',
    medium: '⚡',
  };

  // Dados padrão se não houver carregamento
  const displayStats = {
    todayAlerts: stats?.total_alertas || 0,
    candidatesMonitored: stats?.total_monitorados || 0,
    newPosts: stats?.total_amostra || 0,
  };

  return (
    <div className="space-y-10">
      {/* Main Hero */}
      <div className="border-b border-border-main pb-6">
        <div className="flex flex-col md:flex-row items-start gap-6">
          <div className="flex-shrink-0 w-12 h-12 md:w-16 md:h-16 rounded-xl bg-gradient-to-br from-brand-primary/10 to-blue-500/10 border border-border-main flex items-center justify-center text-2xl shadow-sm">
            📊
          </div>
          <div className="flex-1 space-y-2">
            <div>
              <p className="text-[10px] md:text-xs font-black text-brand-primary uppercase tracking-[0.25em] mb-1">
                Observatório de Discurso Cívico
              </p>
              <h1 className="text-sm sm:text-base md:text-lg lg:text-xl font-bold text-text-main leading-tight tracking-tight uppercase whitespace-nowrap">
                Tendências no Discurso Político Brasileiro
              </h1>
            </div>
            <p className="text-xs md:text-sm text-text-muted max-w-4xl leading-relaxed opacity-80 font-medium">
              Acompanhe em tempo real os padrões de discurso de hostilidade, insultos e ataques a instituições nas redes sociais de candidatos e políticos monitorados.
            </p>
          </div>
        </div>
      </div>


      {/* Today's Stats - 4 Columns High Density Dashboard */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Amostra Total */}
        <div className="bg-bg-card border border-border-main rounded-lg p-3 hover:border-brand-primary/20 transition-all shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            <span className="text-[9px] font-mono text-text-muted uppercase tracking-wider">Posts Processados</span>
          </div>
          <div className="text-lg sm:text-xl font-extrabold text-text-main font-mono">
            {isLoading ? '...' : displayStats.newPosts.toLocaleString('pt-BR')}
          </div>
          <p className="text-[9px] text-text-muted mt-1">Amostra total coletada</p>
        </div>

        {/* KPI 2: Alertas de Ódio */}
        <div className="bg-bg-card border border-border-main rounded-lg p-3 hover:border-brand-primary/20 transition-all shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-[9px] font-mono text-text-muted uppercase tracking-wider">Discursos Hostis</span>
          </div>
          <div className="text-lg sm:text-xl font-extrabold text-text-main font-mono">
            {isLoading ? '...' : displayStats.todayAlerts.toLocaleString('pt-BR')}
          </div>
          <p className="text-[9px] text-text-muted mt-1">Classificados via MCA v2.2</p>
        </div>

        {/* KPI 3: Resiliência Cívica com Barra */}
        <div className="bg-bg-card border border-border-main rounded-lg p-3 hover:border-brand-primary/20 transition-all shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span className="text-[9px] font-mono text-text-muted uppercase tracking-wider">Resiliência</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <div className="text-lg sm:text-xl font-extrabold text-text-main font-mono">
              {isLoading ? '...' : `${stats?.resiliencia || 0}%`}
            </div>
            <span className="text-[9px] text-emerald-500 font-bold">Saudável</span>
          </div>
          {/* Mini progress bar */}
          <div className="w-full bg-bg-main rounded-full h-1 mt-2 overflow-hidden border border-border-main/30">
            <div 
              className="bg-emerald-500 h-full rounded-full transition-all duration-500" 
              style={{ width: `${stats?.resiliencia || 0}%` }}
            />
          </div>
        </div>

        {/* KPI 4: Alvos Monitorados */}
        <div className="bg-bg-card border border-border-main rounded-lg p-3 hover:border-brand-primary/20 transition-all shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-500" />
              <span className="text-[9px] font-mono text-text-muted uppercase tracking-wider">Monitorados</span>
            </div>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <div className="text-lg sm:text-xl font-extrabold text-text-main font-mono">
            {isLoading ? '...' : displayStats.candidatesMonitored}
          </div>
          <p className="text-[9px] text-text-muted mt-1">Perfis ativos sob escrutínio</p>
        </div>
      </div>

      {/* Today's Highlight */}
      {todayHighlight && (
        <div className={`rounded-lg border-2 p-6 transition-all ${severityColor[todayHighlight.severity]}`}>
          <div className="flex items-start gap-4">
            <div className="text-3xl">{severityIcon[todayHighlight.severity]}</div>
            <div className="flex-1">
              <h3 className="text-lg font-bold mb-2">{todayHighlight.title}</h3>
              <p className="text-sm opacity-90">{todayHighlight.description}</p>
              <div className="mt-4 flex gap-2">
                <button className="px-3 py-1 bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 rounded text-sm font-mono transition-colors">
                  Ver Detalhes
                </button>
                <button className="px-3 py-1 bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 rounded text-sm font-mono transition-colors">
                  Compartilhar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded p-3">
          <p className="text-sm text-red-600 dark:text-red-400 font-mono">
            Aviso: Alguns dados não puderam ser carregados. Verificando conectividade...
          </p>
        </div>
      )}
    </div>
  );
}
