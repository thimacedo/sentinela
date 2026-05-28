'use client';

import { useState } from 'react';
import Link from 'next/link';
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
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    if (!todayHighlight) return;
    const shareText = `Sentinela: ${todayHighlight.title} - ${todayHighlight.description} Acompanhe em tempo real: ${typeof window !== 'undefined' ? window.location.origin : 'https://sentinela.democratica'}`;
    
    try {
      await navigator.clipboard.writeText(shareText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Erro ao copiar texto:', err);
    }
  };

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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">
            Tendências no Discurso Político Brasileiro
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Observatório de Discurso Cívico. Acompanhe em tempo real os padrões de discurso monitorados.
          </p>
        </div>
      </div>


      {/* Today's Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-bg-card border border-border-main rounded-lg p-4 hover:border-brand-primary/30 transition-all shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="text-xs font-mono text-text-muted uppercase">Alertas Acumulados</span>
          </div>
          <div className="text-3xl font-bold text-text-main">
            {isLoading ? '...' : displayStats.todayAlerts.toLocaleString('pt-BR')}
          </div>
          <p className="text-xs text-text-muted mt-2">Casos com ódio identificados</p>
        </div>

        <div className="bg-bg-card border border-border-main rounded-lg p-4 hover:border-brand-primary/30 transition-all shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <Users className="w-5 h-5 text-emerald-500" />
            <span className="text-xs font-mono text-text-muted uppercase">Monitorados</span>
          </div>
          <div className="text-3xl font-bold text-text-main">
            {isLoading ? '...' : displayStats.candidatesMonitored}
          </div>
          <p className="text-xs text-text-muted mt-2">Candidatos sob observação</p>
        </div>

        <div className="bg-bg-card border border-border-main rounded-lg p-4 hover:border-brand-primary/30 transition-all shadow-sm">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            <span className="text-xs font-mono text-text-muted uppercase">Posts Processados</span>
          </div>
          <div className="text-3xl font-bold text-text-main">
            {isLoading ? '...' : (displayStats.newPosts / 1000).toFixed(1)}k
          </div>
          <p className="text-xs text-text-muted mt-2">Total coletados</p>
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
                <Link
                  href="/metodologia"
                  className="px-3 py-1 bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 rounded text-sm font-mono transition-colors inline-block"
                >
                  Ver Detalhes
                </Link>
                <button
                  onClick={handleShare}
                  className="px-3 py-1 bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 rounded text-sm font-mono transition-colors"
                >
                  {copied ? 'Copiado! 📋' : 'Compartilhar'}
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
