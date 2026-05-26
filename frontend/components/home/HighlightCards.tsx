'use client';

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
  const { data: alerts = [], isLoading, error } = useAlerts(15);

  // Agrupar e garantir unicidade de candidatos nos destaques
  const candidateAlertsMap = new Map<string, any[]>();
  (alerts as any[]).forEach((alert: any) => {
    const candidate = alert.candidatos?.username || alert.candidato_id || 'Desconhecido';
    if (!candidateAlertsMap.has(candidate)) {
      candidateAlertsMap.set(candidate, []);
    }
    candidateAlertsMap.get(candidate)!.push(alert);
  });

  const processedAlerts = Array.from(candidateAlertsMap.entries())
    .slice(0, 4) // Exibe no máximo 4 candidatos únicos em destaque
    .map(([candidate, candAlerts], idx: number) => {
      const mainAlert = candAlerts[0];
      return {
        id: `${idx}`,
        candidate: candidate,
        title: `Incidência de Discurso em Perfil`,
        summary: mainAlert.texto_bruto?.substring(0, 100) + '...' || 'Análise de toxicidade em andamento',
        alertCount: candAlerts.length,
        severity:
          (mainAlert.categoria_ia === 'CRITICO' ? 'critical' : mainAlert.categoria_ia === 'ELEVADO' ? 'high' : 'medium') as any,
        timestamp: new Date(mainAlert.data_coleta).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) + ' - ' + new Date(mainAlert.data_coleta).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
        topWords: Array.from(new Set(candAlerts.map(a => a.categoria_ia).filter(Boolean))),
      };
    });

  const stories = mockStories || processedAlerts;

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/5 border-red-500/10 hover:border-red-500/30';
      case 'high':
        return 'bg-orange-500/5 border-orange-500/10 hover:border-orange-500/30';
      case 'medium':
        return 'bg-yellow-500/5 border-yellow-500/10 hover:border-yellow-500/30';
      default:
        return 'bg-bg-card border-border-main hover:border-brand-primary/20';
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
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-border-main/50 pb-2">
          <h2 className="text-sm sm:text-base font-bold text-text-main tracking-tight uppercase">📰 Destaques Hoje</h2>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded p-3">
          <p className="text-xs text-red-600 dark:text-red-400 font-mono">
            Erro ao carregar destaques. Verifique conectividade com o backend.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b border-border-main/50 pb-2">
        <h2 className="text-sm sm:text-base font-bold text-text-main tracking-tight uppercase flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-brand-primary rounded-full" />
          📰 Destaques Recentes
        </h2>
        <button className="text-xs text-brand-primary hover:underline font-mono font-bold">
          Ver tudo →
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-6">
          <p className="text-text-muted font-mono text-xs animate-pulse">Carregando destaques...</p>
        </div>
      ) : stories.length === 0 ? (
        <div className="text-center py-6 bg-bg-card border border-border-main rounded p-4">
          <p className="text-text-muted font-mono text-xs">Nenhum alerta recente encontrado</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {stories.map((story) => {
            const badge = getSeverityBadge(story.severity);
            return (
              <article
                key={story.id}
                className={`rounded-lg border p-4 transition-all duration-200 hover:shadow-sm cursor-pointer ${getSeverityStyle(
                  story.severity
                )}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-bg-main border border-border-main flex items-center justify-center text-xs font-bold text-text-muted">
                      {story.candidate.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-xs text-text-main font-bold font-mono">@{story.candidate}</p>
                      <p className="text-[10px] text-text-muted">{story.timestamp}</p>
                    </div>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${badge.color}`}>
                    {badge.label}
                  </span>
                </div>

                <h3 className="text-xs font-bold text-text-main mb-1 truncate">{story.title}</h3>
                <p className="text-text-muted text-xs mb-3 leading-relaxed line-clamp-2">{story.summary}</p>

                <div className="flex flex-wrap gap-1.5 mb-3">
                  {story.topWords?.map((word, idx) => (
                    <span
                      key={idx}
                      className="px-1.5 py-0.5 bg-bg-main text-text-muted text-[8px] uppercase tracking-wider rounded font-mono border border-border-main/50"
                    >
                      {word}
                    </span>
                  ))}
                </div>

                <div className="flex items-center justify-between text-[10px] text-text-muted pt-2 border-t border-border-main/20">
                  <span className="font-mono">{story.alertCount} ocorrência(s) recente(s)</span>
                  <span className="text-brand-primary hover:underline font-mono font-bold text-[9px] flex items-center gap-0.5">
                    Analisar Perícia →
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
