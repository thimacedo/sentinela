'use client';

import { BarChart3, TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react';
import { useCandidates } from '@/hooks/useDashboardData';

interface CandidateMetric {
  label: string;
  value: number;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
}

interface CandidateProfileProps {
  candidateName?: string;
  party?: string;
  position?: string;
  photo?: string;
}

export default function CandidateProfile({
  candidateName,
  party,
  position,
  photo,
}: CandidateProfileProps) {
  const { data: candidates = [], isLoading, error } = useCandidates(5);

  // Se candidato específico é passado, usa esse, senão mostra o primeiro da lista
  const candidateData = candidateName
    ? (candidates as any[]).find((c: any) => c.username === candidateName)
    : (candidates as any[])[0];

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6">
        <p className="text-sm text-red-400 font-mono">
          Erro ao carregar perfis de candidatos.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
        <div className="text-center py-8">
          <p className="text-slate-500 font-mono text-sm animate-pulse">Carregando perfis...</p>
        </div>
      </div>
    );
  }

  if (!candidateData) {
    return (
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
        <p className="text-slate-400 font-mono text-sm">Nenhum candidato encontrado</p>
      </div>
    );
  }

  const metrics: CandidateMetric[] = [
    {
      label: 'Comentários',
      value: candidateData.comentarios_odio_count || 0,
      trend: 'up',
      trendValue: 15,
    },
    {
      label: 'Nível de Risco',
      value: Math.round(candidateData.score_risco * 100) || 0,
      trend: 'up',
      trendValue: 8,
    },
    {
      label: 'Categorias',
      value: Object.keys(candidateData.breakdown || {}).length,
      trend: 'stable',
    },
  ];

  const recentAlerts = [
    {
      severity: (candidateData.nivel_risco === 'CRITICO' ? 'critical' : 'high') as const,
      title: `Nível ${candidateData.nivel_risco}`,
      date: 'Atualizado agora',
    },
  ];

  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-colors">
      {/* Header */}
      <div className="flex gap-6 mb-6">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {photo ? (
            <img
              src={photo}
              alt={candidateData.username}
              className="w-20 h-20 rounded-lg object-cover border border-slate-700"
            />
          ) : (
            <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500/30 to-emerald-500/30 border border-slate-700 flex items-center justify-center text-2xl font-bold text-slate-400">
              {candidateData.username?.substring(0, 2).toUpperCase()}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white mb-1">{candidateData.username}</h3>
          {party && (
            <p className="text-sm text-slate-400 font-mono mb-3">
              {party} {position && `• ${position}`}
            </p>
          )}
          <p className="text-xs text-slate-500">
            Monitorado desde: {new Date(candidateData.data_criacao).toLocaleDateString('pt-BR')}
          </p>
        </div>

        {/* Quick Status */}
        <div className="text-right">
          <div className="bg-slate-800/50 border border-slate-700 rounded p-3">
            <p className="text-xs text-slate-500 mb-1 font-mono">STATUS</p>
            <p
              className={`text-lg font-bold ${
                candidateData.status_monitoramento === 'Ativo'
                  ? 'text-emerald-400'
                  : 'text-slate-400'
              }`}
            >
              {candidateData.status_monitoramento === 'Ativo' ? '✓' : '−'} Ativo
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        {metrics.map((metric, idx) => (
          <div key={idx} className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <p className="text-xs text-slate-500 mb-2 font-mono">{metric.label}</p>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-bold text-white">{metric.value}</p>
              {metric.trend && (
                <div
                  className={`flex items-center gap-1 text-xs font-mono ${
                    metric.trend === 'up'
                      ? 'text-red-400'
                      : metric.trend === 'down'
                        ? 'text-green-400'
                        : 'text-slate-400'
                  }`}
                >
                  {metric.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                  {metric.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                  {metric.trendValue && <span>{metric.trendValue}%</span>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Alerts */}
      {recentAlerts && recentAlerts.length > 0 && (
        <div className="border-t border-slate-700 pt-6">
          <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            Status
          </h4>
          <div className="space-y-2">
            {recentAlerts.map((alert, idx) => (
              <div
                key={idx}
                className={`text-xs p-2 rounded border ${
                  alert.severity === 'critical'
                    ? 'bg-red-500/10 border-red-500/30 text-red-400'
                    : 'bg-orange-500/10 border-orange-500/30 text-orange-400'
                }`}
              >
                <p className="font-mono">{alert.title}</p>
                <p className="text-xs opacity-75">{alert.date}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-colors">
      {/* Header */}
      <div className="flex gap-6 mb-6">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {photo ? (
            <img
              src={photo}
              alt={candidateName}
              className="w-20 h-20 rounded-lg object-cover border border-slate-700"
            />
          ) : (
            <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-blue-500/30 to-emerald-500/30 border border-slate-700 flex items-center justify-center text-2xl font-bold text-slate-400">
              {candidateName.substring(0, 2).toUpperCase()}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white mb-1">{candidateName}</h3>
          {party && (
            <p className="text-sm text-slate-400 font-mono mb-3">
              {party} {position && `• ${position}`}
            </p>
          )}
          <p className="text-xs text-slate-500">
            {monitoringSince && `Monitorado desde: ${monitoringSince}`}
          </p>
        </div>

        {/* Quick Status */}
        <div className="text-right">
          <div className="bg-slate-800/50 border border-slate-700 rounded p-3">
            <p className="text-xs text-slate-500 mb-1 font-mono">STATUS ATUAL</p>
            <p className="text-lg font-bold text-emerald-400">✓ Ativo</p>
          </div>
        </div>
      </div>

      {/* Bio */}
      {bio && (
        <div className="mb-6 pb-6 border-b border-slate-700">
          <p className="text-sm text-slate-300">{bio}</p>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        {metrics.map((metric, idx) => (
          <div key={idx} className="bg-slate-800/30 border border-slate-700 rounded p-3">
            <p className="text-xs text-slate-500 mb-2 font-mono">{metric.label}</p>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-bold text-white">{metric.value}</p>
              {metric.trend && (
                <div
                  className={`flex items-center gap-1 text-xs font-mono ${
                    metric.trend === 'up'
                      ? 'text-red-400'
                      : metric.trend === 'down'
                        ? 'text-green-400'
                        : 'text-slate-400'
                  }`}
                >
                  {metric.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                  {metric.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                  {metric.trendValue && <span>{metric.trendValue}%</span>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Alerts */}
      {recentAlerts && recentAlerts.length > 0 && (
        <div className="border-t border-slate-700 pt-6">
          <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            Alertas Recentes
          </h4>
          <div className="space-y-2">
            {recentAlerts.slice(0, 3).map((alert, idx) => (
              <div
                key={idx}
                className={`text-xs p-2 rounded border ${
                  alert.severity === 'critical'
                    ? 'bg-red-500/10 border-red-500/30 text-red-400'
                    : alert.severity === 'high'
                      ? 'bg-orange-500/10 border-orange-500/30 text-orange-400'
                      : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                }`}
              >
                <p className="font-mono">{alert.title}</p>
                <p className="text-xs opacity-75">{alert.date}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
