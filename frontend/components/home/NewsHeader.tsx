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
    <div className="space-y-6 bg-gradient-to-br from-bg-card to-transparent border border-border-main p-8 md:p-10 rounded-3xl shadow-xl relative overflow-hidden glass-card">
      <div className="absolute top-0 right-0 w-64 h-64 bg-red-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 via-orange-500 to-transparent opacity-80" />

      {/* Main Hero */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-500/10 text-red-500 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 border border-red-500/20">
            <AlertTriangle className="w-3 h-3 animate-pulse" /> Status: Monitoramento Ativo
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-text-main tracking-tighter uppercase leading-none">
            Visão <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-pink-500">Tática Global</span>
          </h1>
          <p className="text-sm md:text-base text-text-muted mt-4 font-medium max-w-2xl leading-relaxed">
            Observatório de Discurso Cívico em tempo real. Padrões de comportamento anômalo e ações coordenadas detectadas via Protocolo PASA.
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mt-6 relative z-10 backdrop-blur-sm">
          <p className="text-sm text-red-600 dark:text-red-400 font-mono flex items-center gap-2 font-bold uppercase tracking-widest">
            <AlertTriangle className="w-4 h-4" /> Falha de Conectividade Detectada.
          </p>
        </div>
      )}
    </div>
  );
}
