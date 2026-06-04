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
    <div className={`rounded-3xl border p-8 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 glass-card relative overflow-hidden group ${style.bg} ${style.border}`}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-current opacity-[0.03] rounded-full -mr-16 -mt-16 blur-xl group-hover:opacity-[0.06] transition-opacity" />
      
      <div className="flex items-start gap-5 relative z-10">
        {/* Icon */}
        <div className="flex-shrink-0 mt-1 bg-bg-main p-3 rounded-2xl shadow-inner border border-border-main">
          <Icon className={`w-7 h-7 ${style.accent}`} />
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-xl font-black text-text-main tracking-tight uppercase">{title}</h3>
            <span className={`px-2.5 py-1 rounded-lg text-[9px] font-mono font-black uppercase tracking-widest border border-current/20 ${style.badge}`}>
              {typeLabel}
            </span>
          </div>

          {/* Main Description */}
          <p className="text-text-muted text-sm mb-6 leading-relaxed font-medium">{description}</p>

          {/* Metric Display */}
          {metric !== undefined && metricLabel && (
            <div className="bg-bg-main/50 border border-border-main rounded-2xl p-5 mb-6 backdrop-blur-sm">
              <p className="text-[9px] text-text-muted mb-2 font-black uppercase tracking-widest">{metricLabel}</p>
              <p className="text-4xl font-black text-text-main tabular-nums tracking-tighter">{metric}%</p>
            </div>
          )}

          {/* Insight Box */}
          <div className="bg-bg-card border-l-4 border-brand-primary/60 pl-5 py-4 mb-6 rounded-r-2xl shadow-sm">
            <p className="text-sm text-text-main italic leading-relaxed">
              <strong className="text-brand-primary not-italic mr-2 font-black uppercase tracking-widest text-[10px]">Insight Analítico:</strong> {insight}
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
