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
    <div className="space-y-3">
      <div className="flex items-center justify-between border-b border-border-main/50 pb-2">
        <h2 className="text-sm sm:text-base font-bold text-text-main tracking-tight uppercase flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-brand-primary rounded-full" />
          📅 Linha do Tempo
        </h2>
        <div className="flex gap-1.5">
          <button className="px-2 py-0.5 text-[10px] font-mono bg-bg-card hover:bg-bg-main border border-border-main rounded transition-colors cursor-pointer">
            24h
          </button>
          <button className="px-2 py-0.5 text-[10px] font-mono bg-bg-card hover:bg-bg-main border border-border-main rounded transition-colors cursor-pointer">
            7d
          </button>
          <button className="px-2 py-0.5 text-[10px] font-mono bg-bg-card hover:bg-bg-main border border-border-main rounded transition-colors cursor-pointer">
            30d
          </button>
        </div>
      </div>

      <p className="text-[10px] text-text-muted">
        Histórico e picos de ocorrência em ordem cronológica ({getPeriodLabel()})
      </p>

      {events.length === 0 ? (
        <div className="text-center py-8 bg-bg-card border border-border-main border-dashed rounded-xl">
          <p className="text-text-muted font-mono text-xs italic">Nenhum evento detectado no radar para este período.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {events.map((event, idx) => (
            <div key={event.id} className="flex gap-4">
              {/* Timeline Connector */}
              <div className="flex flex-col items-center">
                {/* Dot */}
                <div className={`w-3 h-3 rounded-full ${getAlertColor(event.alertLevel)} border-2 border-bg-main z-10 shadow-sm`} />
                {/* Vertical Line */}
                {idx < events.length - 1 && (
                  <div className={`w-0.5 h-16 mt-1.5 ${getAlertColor(event.alertLevel)}/20 rounded-full`} />
                )}
              </div>

              {/* Event Content */}
              <div className="pb-4 pt-0.5 flex-1">
                <div className="bg-bg-card border border-border-main rounded-xl p-3.5 hover:border-brand-primary/20 transition-all">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-[9px] text-text-muted font-mono uppercase tracking-wider mb-0.5">
                        {event.timestamp}
                      </p>
                      <h4 className="text-xs font-bold text-text-main">{event.title}</h4>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono font-bold ${getAlertColor(event.alertLevel)} text-white uppercase`}>
                        {event.postsCount} posts
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-text-muted mb-3 leading-relaxed">{event.description}</p>

                  <div className="flex items-center justify-between text-[10px] text-text-muted pt-2.5 border-t border-border-main/20">
                    <span className="font-mono">
                      Alvo: <strong className="text-text-main">@{event.candidate}</strong>
                    </span>
                    {event.engagementMetric && (
                      <span className="font-mono text-[9px]">
                        Risco Calculado: <strong className="text-red-500 font-bold">{event.engagementMetric}%</strong>
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
