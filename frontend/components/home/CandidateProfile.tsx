'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */

import { AlertTriangle, ChevronLeft, ChevronRight, MessageSquare, Flame, Tags } from 'lucide-react';
import { useCandidates } from '@/hooks/useDashboardData';
import { useState } from 'react';

interface CandidateProfileProps {
  candidateName?: string;
  party?: string;
  position?: string;
  photo?: string;
  bio?: string;
}

export default function CandidateProfile({
  candidateName,
  party,
  position,
  photo,
  bio,
}: CandidateProfileProps) {
  const { data: candidates = [], isLoading, error } = useCandidates(15);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Se candidato específico é passado, usa esse, senão usa o estado do carousel
  const candidateData = candidateName
    ? (candidates as any[]).find((c: any) => c.username === candidateName)
    : (candidates as any[])[currentIndex];

  const handleNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev + 1) % candidates.length);
  };

  const handlePrev = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev - 1 + candidates.length) % candidates.length);
  };

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6">
        <p className="text-sm text-red-600 dark:text-red-400 font-mono">
          Erro ao carregar perfis de candidatos.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-bg-card border border-border-main rounded-xl p-6 shadow-sm">
        <div className="text-center py-12">
          <p className="text-text-muted font-mono text-sm animate-pulse">Carregando perfis...</p>
        </div>
      </div>
    );
  }

  if (!candidateData) {
    return (
      <div className="bg-bg-card border border-border-main rounded-xl p-6 shadow-sm">
        <p className="text-text-muted font-mono text-sm">Nenhum candidato encontrado no monitoramento.</p>
      </div>
    );
  }

  // Fallback dinâmico caso o backend não envie score_risco ou envie 0 por falha na contagem de totais
  let baseScore = 0;
  if (typeof candidateData.score_risco === 'number' && candidateData.score_risco > 0) {
    baseScore = candidateData.score_risco <= 1 ? Math.round(candidateData.score_risco * 100) : Math.round(candidateData.score_risco);
  } else if (candidateData.nivel_risco === 'CRITICO') {
    baseScore = 95;
  } else if (candidateData.nivel_risco === 'ELEVADO') {
    baseScore = 75;
  } else if (candidateData.comentarios_odio_count > 0) {
    baseScore = Math.min(98, 30 + (candidateData.comentarios_odio_count * 5));
  }

  const metrics = [
    {
      label: 'Incidentes Detectados',
      value: candidateData.comentarios_odio_count || 0,
      icon: MessageSquare,
      context: 'comentários hostis validados',
      color: 'text-orange-500',
      isScore: false,
    },
    {
      label: 'Score de Ameaça', // Alterado para quebrar cache visual
      value: baseScore,
      icon: Flame,
      context: 'índice de periculosidade',
      color: baseScore > 80 ? 'text-red-500' : baseScore > 50 ? 'text-orange-500' : 'text-emerald-500',
      isScore: true,
    },
    {
      label: 'Vetores de Ataque',
      value: Object.keys(candidateData.breakdown || {}).length,
      icon: Tags,
      context: 'categorias de ódio distintas',
      color: 'text-brand-primary',
      isScore: false,
    },
  ];

  const recentAlerts = [
    {
      severity: (candidateData.nivel_risco === 'CRITICO' ? 'critical' : 'high') as 'critical' | 'high',
      title: `Nível ${candidateData.nivel_risco}`,
      date: 'Atualizado agora',
    },
  ];

  return (
    <div className="bg-bg-card border border-border-main rounded-xl p-8 hover:border-brand-primary/40 transition-all shadow-sm relative group">
      {/* Carousel Controls */}
      {!candidateName && candidates.length > 1 && (
        <>
          <button 
            onClick={handlePrev} 
            className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/90 dark:bg-slate-800/90 border border-border-main flex items-center justify-center z-20 hover:bg-brand-primary hover:text-white transition-all shadow-lg opacity-0 group-hover:opacity-100"
            aria-label="Candidato Anterior"
          >
            <ChevronLeft size={24} />
          </button>
          <button 
            onClick={handleNext} 
            className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/90 dark:bg-slate-800/90 border border-border-main flex items-center justify-center z-20 hover:bg-brand-primary hover:text-white transition-all shadow-lg opacity-0 group-hover:opacity-100"
            aria-label="Próximo Candidato"
          >
            <ChevronRight size={24} />
          </button>
          
          {/* Pagination Indicators */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5 z-20">
            {candidates.slice(0, 8).map((_: any, idx: number) => (
              <div 
                key={idx} 
                className={`w-1.5 h-1.5 rounded-full transition-all ${idx === currentIndex ? 'bg-brand-primary w-4' : 'bg-border-main'}`}
              />
            ))}
          </div>
        </>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row gap-8 mb-8">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {photo ? (
            <img
              src={photo}
              alt={candidateData.username}
              className="w-24 h-24 rounded-2xl object-cover border-2 border-border-main shadow-md"
            />
          ) : (
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-brand-primary/20 to-blue-500/20 border-2 border-border-main flex items-center justify-center text-3xl font-black text-brand-primary shadow-sm">
              {candidateData.username?.substring(0, 2).toUpperCase()}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-3xl font-black text-text-main tracking-tighter">@{candidateData.username}</h3>
            {candidateData.status_monitoramento === 'Ativo' && (
              <span className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold uppercase rounded-full border border-emerald-500/20">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                Ativo
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mb-4">
            {(party || candidateData.partido) && (
              <p className="text-sm text-text-muted font-bold uppercase tracking-widest">
                {party || candidateData.partido} {(position || candidateData.cargo) && <span className="mx-2 opacity-30">|</span>} {position || candidateData.cargo}
              </p>
            )}
            <p className="text-xs text-text-muted opacity-70">
              Monitorado desde: {candidateData.data_criacao ? new Date(candidateData.data_criacao).toLocaleDateString('pt-BR') : 'N/A'}
            </p>
          </div>
          
          {(bio || candidateData.bio) && (
            <p className="text-sm text-text-muted leading-relaxed max-w-2xl">{bio || candidateData.bio}</p>
          )}
        </div>

        {/* Quick Status */}
        <div className="hidden lg:block text-right">
          <div className="bg-bg-main border border-border-main rounded-xl p-4 min-w-[120px] shadow-inner">
            <p className="text-[10px] text-text-muted mb-1 font-mono font-bold uppercase tracking-tighter">Score Risco</p>
            <p className="text-3xl font-black text-text-main">
              {baseScore}
            </p>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {metrics.map((metric, idx) => {
          const IconComponent = metric.icon;
          return (
            <div key={idx} className="bg-bg-main border border-border-main rounded-xl p-4 transition-colors hover:bg-bg-card flex flex-col justify-between h-full min-h-[120px]">
              <div className="flex items-center gap-2 mb-2">
                <IconComponent className={`w-4 h-4 ${metric.color}`} />
                <p className="text-[10px] text-text-muted font-mono font-bold uppercase tracking-wider">{metric.label}</p>
              </div>
              
              <div className="flex-1 flex flex-col justify-end mt-2">
                <div className="flex items-end gap-1">
                  <p className={`text-3xl font-black leading-none ${metric.color}`}>
                    {metric.value}
                  </p>
                  {metric.isScore && (
                    <span className="text-xs font-bold text-text-muted mb-1">/100</span>
                  )}
                </div>
                
                {metric.isScore && (
                  <div className="w-full h-1.5 bg-bg-card rounded-full mt-3 overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-1000 ${
                        metric.value > 80 ? 'bg-red-500' : metric.value > 50 ? 'bg-orange-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${metric.value}%` }}
                    />
                  </div>
                )}
                
                <p className="text-[9px] font-medium text-text-muted mt-2 uppercase tracking-widest opacity-70">
                  {metric.context}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Alerts */}
      {recentAlerts && recentAlerts.length > 0 && (
        <div className="border-t border-border-main pt-6">
          <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            Alertas de Segurança
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recentAlerts.map((alert, idx) => (
              <div
                key={idx}
                className={`text-xs p-3 rounded-lg border flex justify-between items-center ${
                  alert.severity === 'critical'
                    ? 'bg-red-500/5 border-red-500/20 text-red-600 dark:text-red-400'
                    : 'bg-orange-500/5 border-orange-500/20 text-orange-600 dark:text-orange-400'
                }`}
              >
                <div className="font-bold font-mono tracking-tight uppercase">{alert.title}</div>
                <div className="text-[10px] opacity-70 font-mono italic">{alert.date}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
