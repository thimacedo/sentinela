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
        return 'bg-slate-500';
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
      <div className="flex items-center justify-between border-b border-slate-700 pb-4">
        <h2 className="text-2xl font-bold text-white">📅 Linha do Tempo</h2>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-xs font-mono bg-slate-800 hover:bg-slate-700 rounded">
            24h
          </button>
          <button className="px-3 py-1 text-xs font-mono bg-slate-800 hover:bg-slate-700 rounded">
            7d
          </button>
          <button className="px-3 py-1 text-xs font-mono bg-slate-800 hover:bg-slate-700 rounded">
            30d
          </button>
        </div>
      </div>

      <p className="text-sm text-slate-500 mb-6">
        Cronograma de eventos e picos de atividade ({getPeriodLabel()})
      </p>

      <div className="space-y-6">
        {events.map((event, idx) => (
          <div key={event.id} className="flex gap-6">
            {/* Timeline Connector */}
            <div className="flex flex-col items-center">
              {/* Dot */}
              <div className={`w-4 h-4 rounded-full ${getAlertColor(event.alertLevel)} border-2 border-slate-900 z-10`} />
              {/* Vertical Line */}
              {idx < events.length - 1 && (
                <div className={`w-1 h-20 mt-2 ${getAlertColor(event.alertLevel)}/30 rounded-full`} />
              )}
            </div>

            {/* Event Content */}
            <div className="pb-6 pt-0.5 flex-1">
              <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-xs text-slate-500 font-mono mb-1">
                      {event.timestamp}
                    </p>
                    <h4 className="text-base font-bold text-white">{event.title}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-mono ${getAlertColor(event.alertLevel)} text-white`}>
                      {event.postsCount} posts
                    </span>
                  </div>
                </div>

                <p className="text-sm text-slate-400 mb-3">{event.description}</p>

                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-mono">
                    <strong className="text-slate-300">{event.candidate}</strong>
                  </span>
                  {event.engagementMetric && (
                    <span className="font-mono">
                      Engajamento: <strong className="text-emerald-400">{event.engagementMetric}%</strong>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
