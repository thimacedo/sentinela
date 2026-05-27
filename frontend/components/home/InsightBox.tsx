'use client';

import Link from 'next/link';
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
          bg: 'bg-blue-500/5',
          border: 'border-blue-500/20',
          accent: 'text-blue-600 dark:text-blue-400',
          badge: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
        };
      case 'anomaly':
        return {
          icon: AlertCircle,
          bg: 'bg-red-500/5',
          border: 'border-red-500/20',
          accent: 'text-red-600 dark:text-red-400',
          badge: 'bg-red-500/10 text-red-600 dark:text-red-400',
        };
      case 'pattern':
        return {
          icon: Info,
          bg: 'bg-emerald-500/5',
          border: 'border-emerald-500/20',
          accent: 'text-emerald-600 dark:text-emerald-400',
          badge: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
        };
      case 'alert':
        return {
          icon: AlertCircle,
          bg: 'bg-orange-500/5',
          border: 'border-orange-500/20',
          accent: 'text-orange-600 dark:text-orange-400',
          badge: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
        };
      default:
        return {
          icon: Info,
          bg: 'bg-bg-card',
          border: 'border-border-main',
          accent: 'text-text-muted',
          badge: 'bg-bg-main text-text-muted',
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
    <div className={`rounded-xl border-2 p-6 transition-all ${style.bg} ${style.border}`}>
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="flex-shrink-0 mt-1">
          <Icon className={`w-6 h-6 ${style.accent}`} />
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-3 mb-3">
            <h3 className="text-lg font-bold text-text-main">{title}</h3>
            <span className={`px-2 py-1 rounded text-[10px] font-mono font-bold ${style.badge}`}>
              {typeLabel}
            </span>
          </div>

          {/* Main Description */}
          <p className="text-text-muted text-sm mb-4 leading-relaxed">{description}</p>

          {/* Metric Display */}
          {metric !== undefined && metricLabel && (
            <div className="bg-bg-main border border-border-main rounded-lg p-4 mb-5">
              <p className="text-[10px] text-text-muted mb-1 font-mono uppercase tracking-wider">📊 {metricLabel}</p>
              <p className="text-3xl font-black text-text-main">{metric}%</p>
            </div>
          )}

          {/* Insight Box */}
          <div className="bg-bg-card border-l-4 border-brand-primary/40 pl-4 py-3 mb-5 rounded-r-lg">
            <p className="text-sm text-text-main italic leading-relaxed">
              <strong className="text-brand-primary not-italic mr-1">💡 Insight:</strong> {insight}
            </p>
          </div>

          {/* Footer Stats */}
          <div className="flex flex-wrap gap-6 text-[11px] text-text-muted font-mono pt-4 border-t border-border-main/50">
            {confidence && (
              <div className="flex items-center gap-2">
                <span className="opacity-70">CONFIANÇA:</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">{confidence}%</span>
              </div>
            )}
            {sources && (
              <div className="flex items-center gap-2">
                <span className="opacity-70">FONTES:</span>
                <span className="text-blue-600 dark:text-blue-400 font-bold">{sources} posts</span>
              </div>
            )}
            {relatedCandidates && relatedCandidates.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="opacity-70">ENVOLVIDOS:</span>
                <span className="text-orange-600 dark:text-orange-400 font-bold">{relatedCandidates.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Action */}
          <Link
            href="/analise"
            className="mt-6 inline-block px-4 py-2 bg-bg-card hover:bg-bg-main border border-border-main text-text-main rounded-lg text-xs font-mono font-bold transition-all shadow-sm"
          >
            Explorar dados completos →
          </Link>
        </div>
      </div>
    </div>
  );
}
