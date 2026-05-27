'use client';
import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Users, Filter } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import { fetchApi } from '@/lib/api';

interface Target {
  id: string;
  username: string;
  status_monitoramento: string;
  tier: string;
  score_risco: number;
  nivel_risco: string;
  color: string;
  comentarios_odio_count: number;
  breakdown?: Record<string, number>;
}

export default function TargetsTab() {
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [visibleCount, setVisibleCount] = useState(5);
  const observerRef = useRef<HTMLDivElement>(null);

  const { data: targets = [], isLoading } = useQuery<Target[]>({
    queryKey: ['active-targets-enriched'],
    queryFn: async () => {
      return await fetchApi('/api/v1/targets');
    },
    refetchInterval: 60000,
  });

  const filteredTargets = targets.filter((t) => {
    const matchesSearch = t.username.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRisk = riskFilter === 'ALL' || t.nivel_risco === riskFilter;
    return matchesSearch && matchesRisk;
  });

  // Reseta o visibleCount ao mudar os filtros
  useEffect(() => {
    setVisibleCount(5);
  }, [searchQuery, riskFilter]);

  // Observer para o Wall Infinito
  useEffect(() => {
    if (!observerRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => prev + 5);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [filteredTargets.length]);

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-brand-primary" />
            Candidatos Monitorados
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Radar de Severidade e Atividade</p>
        </div>
        <button 
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-3 py-1.5 border rounded-lg text-[10px] font-bold transition-colors uppercase ${showFilters ? 'bg-brand-primary/10 border-brand-primary text-brand-primary' : 'bg-bg-card border-border-main text-text-main hover:bg-bg-main'}`}
        >
          <Filter className="w-3 h-3" />
          Filtrar
        </button>
      </div>

      {/* Painel de Filtros */}
      {showFilters && (
        <div className="p-4 bg-bg-main/30 border-b border-border-main flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Buscar Username</label>
            <input 
              type="text"
              placeholder="Ex: samia"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-1.5 bg-bg-card border border-border-main rounded-lg text-xs text-text-main placeholder:text-text-muted focus:outline-none focus:border-brand-primary transition-colors"
            />
          </div>
          <div className="w-[180px]">
            <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Nível de Risco</label>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="w-full px-3 py-1.5 bg-bg-card border border-border-main rounded-lg text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors"
            >
              <option value="ALL">TODOS</option>
              <option value="CRITICO">CRÍTICO</option>
              <option value="ELEVADO">ELEVADO</option>
              <option value="MONITORANDO">MONITORANDO</option>
              <option value="CONTROLADO">CONTROLADO</option>
            </select>
          </div>
          {(searchQuery || riskFilter !== 'ALL') && (
            <button 
              onClick={() => {
                setSearchQuery('');
                setRiskFilter('ALL');
              }}
              className="mt-5 text-[9px] font-bold text-red-500 hover:underline uppercase tracking-wider"
            >
              Limpar
            </button>
          )}
        </div>
      )}

      {/* Feed de Candidatos */}
      <div className="p-6 space-y-6 bg-bg-main/10">
        {isLoading ? (
          <div className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
            SINCRONIZANDO COM O OBSERVATÓRIO...
          </div>
        ) : filteredTargets.length === 0 ? (
          <div className="text-center py-20 text-text-muted font-mono text-xs">
            NENHUM ALVO ENCONTRADO COM OS FILTROS SELECIONADOS.
          </div>
        ) : (
          <div className="flex flex-col gap-6 max-w-2xl mx-auto">
            {filteredTargets.slice(0, visibleCount).map((t, index) => {
              const totalHate = t.comentarios_odio_count || 0;
              
              return (
                <div key={t.id} className="w-full">
                  {/* Card Estilo Rede Social */}
                  <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200">
                    <div className="flex items-start justify-between gap-4">
                      {/* Avatar e Nome de Usuário */}
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-12 h-12 rounded-full flex items-center justify-center font-black text-white text-base shadow-inner"
                          style={{ backgroundColor: t.color || '#8b5cf6' }}
                        >
                          {t.username.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-black text-text-main text-base tracking-tight hover:underline cursor-pointer">
                            @{t.username}
                          </div>
                          <div className="text-[10px] text-text-muted font-mono mt-0.5 uppercase">
                            ID: {t.id.substring(0, 8)}
                          </div>
                        </div>
                      </div>

                      {/* Status / Risco */}
                      <div className="flex flex-col items-end gap-1.5">
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-[9px] font-black uppercase px-2 py-0.5 rounded-md">
                          {t.status_monitoramento}
                        </Badge>
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-bg-main border border-border-main rounded-full">
                          <div 
                            className="w-1.5 h-1.5 rounded-full animate-pulse" 
                            style={{ backgroundColor: t.color || '#333' }}
                          />
                          <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: t.color || '#333' }}>
                            {t.nivel_risco}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Destaque de Métricas */}
                    <div className="mt-5 grid grid-cols-2 gap-4 border-t border-b border-border-main py-4 bg-bg-main/20 rounded-xl px-4">
                      <div className="text-center">
                        <div className="text-2xl font-black text-text-main">{t.comentarios_odio_count}</div>
                        <div className="text-[9px] font-bold text-text-muted uppercase tracking-wider mt-1">Alertas de Ódio</div>
                      </div>
                      <div className="text-center border-l border-border-main">
                        <div className="text-2xl font-black text-brand-primary">{t.score_risco || 0}%</div>
                        <div className="text-[9px] font-bold text-text-muted uppercase tracking-wider mt-1">Score de Severidade</div>
                      </div>
                    </div>

                    {/* Distribuição de Categorias (Breakdown) */}
                    {t.breakdown && Object.keys(t.breakdown).length > 0 && (
                      <div className="mt-5 space-y-3">
                        <span className="text-[9px] font-black text-text-muted uppercase tracking-widest block">
                          Distribuição de Hostilidade (MCA v2.2)
                        </span>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2.5">
                          {Object.entries(t.breakdown).map(([category, count]) => {
                            const percent = totalHate > 0 ? ((count as number) / totalHate) * 100 : 0;
                            return (
                              <div key={category} className="space-y-1">
                                <div className="flex justify-between text-[10px] font-bold text-text-main/80 uppercase">
                                  <span className="truncate">{category.replace(/_/g, ' ')}</span>
                                  <span>{count as number}</span>
                                </div>
                                <div className="w-full h-1.5 bg-bg-main rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-brand-primary transition-all duration-500" 
                                    style={{ width: `${percent}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* AdSense intercalado a cada 5 cards */}
                  {(index + 1) % 5 === 0 && (
                    <div className="my-6 border border-border-main bg-bg-card rounded-2xl p-4 flex flex-col items-center shadow-sm">
                      <span className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-3">Publicidade Cívica Relacionada</span>
                      <AdSenseSlot adSlot="2020882637" format="horizontal" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Div Observadora de Scroll Infinito */}
        {filteredTargets.length > visibleCount && (
          <div ref={observerRef} className="py-8 flex justify-center items-center">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce" />
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce delay-100" />
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce delay-200" />
              <span className="text-[10px] font-black text-brand-primary uppercase tracking-widest ml-2">
                Carregando mais candidatos...
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-bg-main/30 border-t border-border-main text-center text-xs text-text-muted">
        Exibindo {Math.min(visibleCount, filteredTargets.length)} de {filteredTargets.length} perfis monitorados.
      </div>
    </div>
  );
}
