'use client';

import { AlertCircle, TrendingUp, Info } from 'lucide-react';

interface InsightBoxProps {
  type: 'trend' | 'anomaly' | 'pattern' | 'alert';
  title: string;
  description: string;
  insight: string;
  metric?: number;
  metricLabel?: string;
  confidence?: number;
  relatedCandidates?: string[];
  sources?: number;
}

export default function InsightBox({
  type,
  title,
  description,
  insight,
  metric,
  metricLabel,
  confidence = 85,
  relatedCandidates,
  sources,
}: InsightBoxProps) {
  const getTypeStyle = () => {
    switch (type) {
      case 'trend':
        return {
          icon: TrendingUp,
          bg: 'bg-blue-500/10',
          border: 'border-blue-500/30',
          accent: 'text-blue-400',
          badge: 'bg-blue-500/20 text-blue-400',
        };
      case 'anomaly':
        return {
          icon: AlertCircle,
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          accent: 'text-red-400',
          badge: 'bg-red-500/20 text-red-400',
        };
      case 'pattern':
        return {
          icon: Info,
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/30',
          accent: 'text-emerald-400',
          badge: 'bg-emerald-500/20 text-emerald-400',
        };
      case 'alert':
        return {
          icon: AlertCircle,
          bg: 'bg-orange-500/10',
          border: 'border-orange-500/30',
          accent: 'text-orange-400',
          badge: 'bg-orange-500/20 text-orange-400',
        };
      default:
        return {
          icon: Info,
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/30',
          accent: 'text-slate-400',
          badge: 'bg-slate-500/20 text-slate-400',
        };
    }
  };

  const style = getTypeStyle();
  const Icon = style.icon;

  const typeLabel = {
    trend: 'TENDÊNCIA',
    anomaly: 'ANOMALIA',
    pattern: 'PADRÃO',
    alert: 'ALERTA',
  }[type];

  return (
    <div className={`rounded-lg border-2 p-6 ${style.bg} ${style.border}`}>
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="flex-shrink-0">
          <Icon className={`w-6 h-6 ${style.accent}`} />
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-3 mb-3">
            <h3 className="text-lg font-bold text-white">{title}</h3>
            <span className={`px-2 py-1 rounded text-xs font-mono ${style.badge}`}>
              {typeLabel}
            </span>
          </div>

          {/* Main Description */}
          <p className="text-slate-300 text-sm mb-4">{description}</p>

          {/* Metric Display */}
          {metric !== undefined && metricLabel && (
            <div className="bg-white/5 border border-white/10 rounded p-3 mb-4">
              <p className="text-xs text-slate-500 mb-1">📊 {metricLabel}</p>
              <p className="text-2xl font-bold text-white">{metric}%</p>
            </div>
          )}

          {/* Insight Box */}
          <div className="bg-black/30 border-l-2 border-white/20 pl-3 py-2 mb-4">
            <p className="text-sm text-slate-300 italic">
              <strong>💡 Insight:</strong> {insight}
            </p>
          </div>

          {/* Footer Stats */}
          <div className="flex flex-wrap gap-4 text-xs text-slate-500 font-mono">
            {confidence && (
              <div>
                <span className="text-slate-400">Confiança:</span>
                <span className="ml-2 text-emerald-400">{confidence}%</span>
              </div>
            )}
            {sources && (
              <div>
                <span className="text-slate-400">Fontes:</span>
                <span className="ml-2 text-blue-400">{sources} posts</span>
              </div>
            )}
            {relatedCandidates && relatedCandidates.length > 0 && (
              <div>
                <span className="text-slate-400">Envolvidos:</span>
                <span className="ml-2 text-orange-400">{relatedCandidates.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Action */}
          <button className="mt-4 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded text-xs font-mono transition-colors">
            Explorar dados completos →
          </button>
        </div>
      </div>
    </div>
  );
}
