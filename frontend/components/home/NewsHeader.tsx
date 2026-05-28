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
    <div className="space-y-4">
      {/* Main Hero */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">
            Tendências no Discurso Político Brasileiro
          </h1>
          <p className="text-xs text-text-muted mt-1 font-medium">
            Observatório de Discurso Cívico. Acompanhe em tempo real os padrões de discurso monitorados através do Protocolo PASA.
          </p>
        </div>
      </div>

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
