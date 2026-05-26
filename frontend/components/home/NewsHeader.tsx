'use client';

import { TrendingUp, AlertTriangle, Users } from 'lucide-react';
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
    critical: 'bg-red-500/20 border-red-500/50 text-red-400',
    high: 'bg-orange-500/20 border-orange-500/50 text-orange-400',
    medium: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400',
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
    <div className="space-y-6">
      {/* Main Hero */}
      <div className="border-b border-slate-700 pb-8">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500/20 to-emerald-500/20 border border-blue-500/30 flex items-center justify-center text-xl">
            📊
          </div>
          <div>
            <p className="text-sm font-mono text-slate-500 uppercase tracking-widest mb-2">
              Observatório de Discurso Cívico
            </p>
            <h1 className="text-5xl font-bold text-white leading-tight">
              Tendências no Discurso Político Brasileiro
            </h1>
          </div>
        </div>
        <p className="text-lg text-slate-400 max-w-3xl">
          Acompanhe em tempo real os padrões de discurso de ódio e violência em redes sociais de candidatos e políticos monitorados. Transparência que alimenta a democracia.
        </p>
      </div>

      {/* Today's Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 hover:border-blue-500/30 transition-colors">
          <div className="flex items-center gap-3 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-xs font-mono text-slate-500 uppercase">Alertas Acumulados</span>
          </div>
          <div className="text-3xl font-bold text-white">
            {isLoading ? '...' : displayStats.todayAlerts.toLocaleString('pt-BR')}
          </div>
          <p className="text-xs text-slate-500 mt-2">Casos com ódio identificados</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 hover:border-emerald-500/30 transition-colors">
          <div className="flex items-center gap-3 mb-3">
            <Users className="w-5 h-5 text-emerald-400" />
            <span className="text-xs font-mono text-slate-500 uppercase">Monitorados</span>
          </div>
          <div className="text-3xl font-bold text-white">
            {isLoading ? '...' : displayStats.candidatesMonitored}
          </div>
          <p className="text-xs text-slate-500 mt-2">Candidatos sob observação</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 hover:border-orange-500/30 transition-colors">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp className="w-5 h-5 text-orange-400" />
            <span className="text-xs font-mono text-slate-500 uppercase">Posts Processados</span>
          </div>
          <div className="text-3xl font-bold text-white">
            {isLoading ? '...' : (displayStats.newPosts / 1000).toFixed(1)}k
          </div>
          <p className="text-xs text-slate-500 mt-2">Total coletados</p>
        </div>
      </div>

      {/* Today's Highlight */}
      {todayHighlight && (
        <div className={`rounded-lg border-2 p-6 ${severityColor[todayHighlight.severity]}`}>
          <div className="flex items-start gap-4">
            <div className="text-3xl">{severityIcon[todayHighlight.severity]}</div>
            <div className="flex-1">
              <h3 className="text-lg font-bold mb-2">{todayHighlight.title}</h3>
              <p className="text-sm opacity-90">{todayHighlight.description}</p>
              <div className="mt-4 flex gap-2">
                <button className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-sm font-mono transition-colors">
                  Ver Detalhes
                </button>
                <button className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-sm font-mono transition-colors">
                  Compartilhar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded p-3">
          <p className="text-sm text-red-400 font-mono">
            Aviso: Alguns dados não puderam ser carregados. Verificando conectividade...
          </p>
        </div>
      )}
    </div>
  );
}
