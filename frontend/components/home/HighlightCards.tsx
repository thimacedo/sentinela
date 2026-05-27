'use client';

import Link from 'next/link';
import { useAlerts } from '@/hooks/useDashboardData';

interface HighlightStory {
  id: string;
  candidate: string;
  title: string;
  summary: string;
  alertCount: number;
  severity: 'critical' | 'high' | 'medium';
  timestamp: string;
  topWords?: string[];
}

interface HighlightCardsProps {
  stories?: HighlightStory[];
}

export default function HighlightCards({ stories: mockStories }: HighlightCardsProps) {
  const { data: alerts = [], isLoading, error } = useAlerts(10);

  // Transformar alertas reais em stories
  const processedAlerts = (alerts as any[])
    .slice(0, 5)
    .map((alert: any, idx: number) => ({
      id: `${idx}`,
      candidate: alert.candidatos?.username || 'Desconhecido',
      title: `Discurso de ódio detectado`,
      summary: alert.texto_bruto?.substring(0, 120) + '...' || 'Análise analítica em progresso',
      alertCount: 1,
      severity:
        (alert.categoria_ia === 'CRITICO' ? 'critical' : alert.categoria_ia === 'ELEVADO' ? 'high' : 'medium') as any,
      timestamp: new Date(alert.data_coleta).toLocaleString('pt-BR'),
      topWords: alert.categoria_ia ? [alert.categoria_ia] : ['análise'],
    }));

  const stories = mockStories || processedAlerts;

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/5 border-red-500/20 hover:border-red-500/40';
      case 'high':
        return 'bg-orange-500/5 border-orange-500/20 hover:border-orange-500/40';
      case 'medium':
        return 'bg-yellow-500/5 border-yellow-500/20 hover:border-yellow-500/40';
      default:
        return 'bg-bg-card border-border-main hover:border-brand-primary/40';
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return { label: 'Crítico', color: 'bg-red-500/10 text-red-600 dark:text-red-400' };
      case 'high':
        return { label: 'Alto', color: 'bg-orange-500/10 text-orange-600 dark:text-orange-400' };
      case 'medium':
        return { label: 'Médio', color: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400' };
      default:
        return { label: 'Baixo', color: 'bg-bg-main text-text-muted border border-border-main' };
    }
  };

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border-main pb-4">
          <h2 className="text-2xl font-bold text-text-main">📰 Destaques Hoje</h2>
        </div>
        <div className="bg-red-500/10 border border-red-500/30 rounded p-4">
          <p className="text-sm text-red-600 dark:text-red-400 font-mono">
            Erro ao carregar destaques. Verifique conectividade com o backend.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-border-main pb-4">
        <h2 className="text-2xl font-bold text-text-main">📰 Destaques Recentes</h2>
        <Link href="/alertas" className="text-sm text-brand-primary hover:underline font-mono">
          Ver tudo →
        </Link>
      </div>

      {isLoading ? (
        <div className="text-center py-8">
          <p className="text-text-muted font-mono text-sm animate-pulse">Carregando destaques...</p>
        </div>
      ) : stories.length === 0 ? (
        <div className="text-center py-8 bg-bg-card border border-border-main rounded p-6">
          <p className="text-text-muted font-mono text-sm">Nenhum alerta recente encontrado</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {stories.map((story) => {
            const badge = getSeverityBadge(story.severity);
            return (
              <article
                key={story.id}
                className={`rounded-lg border p-6 transition-all duration-200 hover:shadow-sm cursor-pointer ${getSeverityStyle(
                  story.severity
                )}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-bg-main border border-border-main flex items-center justify-center text-sm font-bold text-text-muted">
                      {story.candidate.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm text-text-main font-bold font-mono">{story.candidate}</p>
                      <p className="text-xs text-text-muted">{story.timestamp}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-mono font-bold ${badge.color}`}>
                    {badge.label}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-text-main mb-2">{story.title}</h3>
                <p className="text-text-muted text-sm mb-4 leading-relaxed">{story.summary}</p>

                <div className="flex flex-wrap gap-2 mb-4">
                  {story.topWords?.map((word, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-bg-main text-text-muted text-[10px] uppercase tracking-wider rounded font-mono border border-border-main"
                    >
                      {word}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs text-text-muted">
                  <span className="font-mono">{story.alertCount} caso(s) identificado(s)</span>
                  <Link href="/analise" className="text-brand-primary hover:underline font-mono font-bold">
                    Explorar Análise →
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
