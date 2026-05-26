'use client';

interface TimelineEvent {
  id: string;
  timestamp: string;
  candidate: string;
  title: string;
  description: string;
  alertLevel: 'critical' | 'high' | 'medium' | 'low';
  postsCount: number;
  engagementMetric?: number;
}

interface EventTimelineProps {
  events: TimelineEvent[];
  period?: '24h' | '7d' | '30d';
}

export default function EventTimeline({ events, period = '24h' }: EventTimelineProps) {
  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      default:
        return 'bg-brand-primary';
    }
  };

  const getPeriodLabel = () => {
    switch (period) {
      case '7d':
        return 'Últimos 7 Dias';
      case '30d':
        return 'Últimos 30 Dias';
      default:
        return 'Últimas 24 Horas';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-border-main pb-4">
        <h2 className="text-2xl font-bold text-text-main">📅 Linha do Tempo</h2>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-xs font-mono bg-bg-card hover:bg-bg-main border border-border-main rounded transition-colors">
            24h
          </button>
          <button className="px-3 py-1 text-xs font-mono bg-bg-card hover:bg-bg-main border border-border-main rounded transition-colors">
            7d
          </button>
          <button className="px-3 py-1 text-xs font-mono bg-bg-card hover:bg-bg-main border border-border-main rounded transition-colors">
            30d
          </button>
        </div>
      </div>

      <p className="text-sm text-text-muted mb-6">
        Cronograma de eventos e picos de atividade ({getPeriodLabel()})
      </p>

      {events.length === 0 ? (
        <div className="text-center py-12 bg-bg-card border border-border-main border-dashed rounded-xl">
          <p className="text-text-muted font-mono text-sm italic">Nenhum evento detectado no radar para este período.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {events.map((event, idx) => (
            <div key={event.id} className="flex gap-6">
              {/* Timeline Connector */}
              <div className="flex flex-col items-center">
                {/* Dot */}
                <div className={`w-4 h-4 rounded-full ${getAlertColor(event.alertLevel)} border-2 border-bg-main z-10 shadow-sm`} />
                {/* Vertical Line */}
                {idx < events.length - 1 && (
                  <div className={`w-0.5 h-24 mt-2 ${getAlertColor(event.alertLevel)}/20 rounded-full`} />
                )}
              </div>

              {/* Event Content */}
              <div className="pb-8 pt-0.5 flex-1">
                <div className="bg-bg-card border border-border-main rounded-xl p-5 hover:border-brand-primary/40 transition-all hover:shadow-md">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-[10px] text-text-muted font-mono uppercase tracking-widest mb-1">
                        {event.timestamp}
                      </p>
                      <h4 className="text-lg font-bold text-text-main">{event.title}</h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-[10px] font-mono font-bold ${getAlertColor(event.alertLevel)} text-white uppercase`}>
                        {event.postsCount} posts
                      </span>
                    </div>
                  </div>

                  <p className="text-sm text-text-muted mb-4 leading-relaxed">{event.description}</p>

                  <div className="flex items-center justify-between text-xs text-text-muted pt-4 border-t border-border-main/50">
                    <span className="font-mono">
                      Candidato: <strong className="text-text-main">@{event.candidate}</strong>
                    </span>
                    {event.engagementMetric && (
                      <span className="font-mono">
                        Engajamento: <strong className="text-emerald-500 font-bold">{event.engagementMetric}%</strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
