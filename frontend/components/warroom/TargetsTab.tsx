'use client';
import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Users, Filter, Plus, Loader2, Search, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import { useWallet } from '@/hooks/useWallet';

interface Target {
  id: string;
  username: string;
  nome_completo?: string;
  cargo?: string;
  partido?: string;
  estado?: string;
  status_monitoramento: string;
  tier: string;
  score_risco: number;
  nivel_risco: string;
  color: string;
  comentarios_odio_count: number;
  comentarios_totais_count?: number;
  breakdown?: Record<string, number>;
}

export default function TargetsTab() {
  const router = useRouter();
  const { balance, refreshBalance } = useWallet();
  const [isAdding, setIsAdding] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [partyFilter, setPartyFilter] = useState('ALL');
  const [stateFilter, setStateFilter] = useState('ALL');
  const [visibleCount, setVisibleCount] = useState(6);
  const observerRef = useRef<HTMLDivElement>(null);

  const { data: targets = [], isLoading, refetch } = useQuery<Target[]>({
    queryKey: ['active-targets-enriched'],
    queryFn: async () => {
      return await fetchApi('/api/v1/targets');
    },
    refetchInterval: 60000,
  });

  const filteredTargets = targets.filter((t) => {
    const matchesSearch = t.username.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         (t.nome_completo?.toLowerCase() || '').includes(searchQuery.toLowerCase());
    const matchesRisk = riskFilter === 'ALL' || t.nivel_risco === riskFilter;
    const matchesParty = partyFilter === 'ALL' || t.partido === partyFilter;
    const matchesState = stateFilter === 'ALL' || t.estado === stateFilter;
    return matchesSearch && matchesRisk && matchesParty && matchesState;
  });

  // Extrair listas únicas para filtros
  const parties = Array.from(new Set(targets.map(t => t.partido).filter(Boolean))).sort() as string[];
  const states = Array.from(new Set(targets.map(t => t.estado).filter(Boolean))).sort() as string[];

  // Observer para o Wall Infinito
  useEffect(() => {
    if (!observerRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => prev + 6);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [filteredTargets.length]);

  const handleAddTarget = async () => {
    setTimeout(async () => {
      if (balance < 500) {
        alert("Aporte Insuficiente. Adquira mais Créditos de Inteligência (CI) para configurar a malha neural para novos perfis.");
        router.push('/planos');
        return;
      }

      const username = prompt("Digite o @ do Instagram do novo alvo (ex: jairbolsonaro):");
      if (!username) return;

      const cleanUsername = username.replace('@', '').trim().toLowerCase();

      const confirmAdd = window.confirm(`Configurar nossa malha neural para monitoramento 24/7 de @${cleanUsername} exige um aporte de 500 CI. Autorizar?`);
      if (!confirmAdd) return;

      try {
        setIsAdding(true);
        const userId = localStorage.getItem('sentinela_user_id');
        
        if (!userId) {
          alert("Sessão inválida. Faça login.");
          return;
        }

        const { data: rpcData, error: rpcError } = await supabase.rpc('process_stn_transaction', {
          p_user_id: userId,
          p_amount: -500,
          p_type: 'CONSUMPTION',
          p_session_id: null,
          p_metadata: { action: 'add_target', target: cleanUsername }
        });

        if (rpcError) throw rpcError;

        if (rpcData === true) {
          await supabase.from('candidatos').insert({
            username: cleanUsername,
            estado: 'BR',
            status_monitoramento: 'Ativo'
          });

          refreshBalance();
          refetch();
          alert(`Alvo @${cleanUsername} injetado com sucesso na malha de coleta.`);
        } else {
          alert("Falha na transação. Saldo insuficiente.");
        }
      } catch (err) {
        console.error(err);
        alert("Erro ao injetar novo alvo.");
      } finally {
        setIsAdding(false);
      }
    }, 0);
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      {/* Header Profissional */}
      <div className="p-6 border-b border-border-main flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2 uppercase">
            <Users className="w-5 h-5 text-brand-primary" />
            Radar de Candidatos
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Inteligência Preditiva e Monitoramento de Hostilidade</p>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
          <button 
            onClick={() => setShowFilters(!showFilters)}
            className={`flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 border rounded-xl text-[10px] font-bold transition-all uppercase ${showFilters ? 'bg-brand-primary/10 border-brand-primary text-brand-primary' : 'bg-bg-card border-border-main text-text-main hover:bg-bg-main shadow-sm'}`}
          >
            <Filter className="w-3 h-3" />
            {showFilters ? 'Fechar Filtros' : 'Filtrar Alvos'}
          </button>
          <button 
            onClick={handleAddTarget}
            disabled={isAdding}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-xl text-[10px] font-black hover:bg-brand-primary/90 transition-all uppercase shadow-lg shadow-brand-primary/20 disabled:opacity-50"
          >
            {isAdding ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
            Novo Alvo (500 CI)
          </button>
        </div>
      </div>

      {/* Painel de Filtros Avançados */}
      {showFilters && (
        <div className="p-5 bg-bg-main/30 border-b border-border-main grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-end animate-in slide-in-from-top-2 duration-300">
          <div className="space-y-1.5">
            <label className="text-[9px] font-bold text-text-muted uppercase tracking-wider flex items-center gap-1">
              <Search className="w-2.5 h-2.5" /> Pesquisar
            </label>
            <input 
              type="text"
              placeholder="Username ou Nome..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setVisibleCount(6);
              }}
              className="w-full px-3 py-2 bg-bg-card border border-border-main rounded-xl text-xs text-text-main placeholder:text-text-muted focus:outline-none focus:border-brand-primary transition-colors"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Severidade de Risco</label>
            <select
              value={riskFilter}
              onChange={(e) => {
                setRiskFilter(e.target.value);
                setVisibleCount(6);
              }}
              className="w-full px-3 py-2 bg-bg-card border border-border-main rounded-xl text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors appearance-none"
            >
              <option value="ALL">TODOS OS NÍVEIS</option>
              <option value="CRITICO">🔴 CRÍTICO</option>
              <option value="ELEVADO">🟠 ELEVADO</option>
              <option value="MONITORANDO">🔵 MONITORANDO</option>
              <option value="CONTROLADO">🟢 CONTROLADO</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Partido</label>
            <select
              value={partyFilter}
              onChange={(e) => {
                setPartyFilter(e.target.value);
                setVisibleCount(6);
              }}
              className="w-full px-3 py-2 bg-bg-card border border-border-main rounded-xl text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors appearance-none"
            >
              <option value="ALL">TODOS OS PARTIDOS</option>
              {parties.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Estado (UF)</label>
            <select
              value={stateFilter}
              onChange={(e) => {
                setStateFilter(e.target.value);
                setVisibleCount(6);
              }}
              className="w-full px-3 py-2 bg-bg-card border border-border-main rounded-xl text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors appearance-none"
            >
              <option value="ALL">TODAS AS UFs</option>
              {states.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {(searchQuery || riskFilter !== 'ALL' || partyFilter !== 'ALL' || stateFilter !== 'ALL') && (
            <button 
              onClick={() => {
                setSearchQuery('');
                setRiskFilter('ALL');
                setPartyFilter('ALL');
                setStateFilter('ALL');
              }}
              className="sm:col-span-full md:col-span-4 text-[9px] font-black text-red-500 hover:text-red-600 transition-colors uppercase tracking-widest flex items-center justify-center gap-1 mt-2"
            >
              <X className="w-3 h-3" /> Limpar Filtros Avançados
            </button>
          )}
        </div>
      )}

      {/* Feed de Candidatos em Grid 2 Colunas */}
      <div className="p-6 bg-bg-main/10 min-h-[400px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 text-text-muted gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
            <span className="animate-pulse font-mono text-[10px] uppercase tracking-widest">Sincronizando Malha Neural...</span>
          </div>
        ) : filteredTargets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 text-text-muted border-2 border-dashed border-border-main rounded-3xl">
            <Users className="w-12 h-12 mb-4 opacity-20" />
            <span className="font-mono text-[10px] uppercase tracking-widest">Nenhum alvo localizado nesta frequência.</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl mx-auto">
            {filteredTargets.slice(0, visibleCount).map((t) => {
              const totalHate = t.comentarios_odio_count || 0;
              const totalComms = t.comentarios_totais_count || 0;
              const healthScore = Math.max(0, 100 - t.score_risco);
              
              return (
                <div 
                  key={t.id} 
                  onClick={() => router.push(`/analise?target=${t.username}`)}
                  className="group relative bg-bg-card border border-border-main rounded-3xl p-6 shadow-sm hover:shadow-2xl hover:border-brand-primary/40 hover:-translate-y-1 transition-all duration-500 cursor-pointer overflow-hidden"
                >
                  {/* Background Glass Effect */}
                  <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary/5 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-brand-primary/10 transition-colors duration-500" />
                  
                  <div className="flex items-start justify-between gap-4 relative z-10">
                    <div className="flex items-center gap-4">
                      {/* Avatar Squad */}
                      <div className="relative">
                        <div 
                          className="w-16 h-16 rounded-2xl flex items-center justify-center font-black text-white text-2xl shadow-lg transform group-hover:rotate-3 transition-all duration-500"
                          style={{ backgroundColor: t.color || '#8b5cf6' }}
                        >
                          {t.username.substring(0, 2).toUpperCase()}
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-bg-card border border-border-main rounded-lg flex items-center justify-center shadow-sm">
                           <span className="text-[8px] font-black text-brand-primary leading-none">{t.estado}</span>
                        </div>
                      </div>

                      <div className="space-y-0.5">
                        <div className="font-black text-text-main text-xl tracking-tighter group-hover:text-brand-primary transition-colors flex items-center gap-1.5">
                          @{t.username}
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                        </div>
                        {t.nome_completo && (
                          <div className="text-[11px] text-text-muted font-bold uppercase tracking-tight truncate max-w-[180px]">
                            {t.nome_completo}
                          </div>
                        )}
                        <div className="flex items-center gap-2 mt-1.5">
                          {t.partido && (
                            <Badge className="bg-brand-primary/10 text-brand-primary border-none text-[8px] font-black uppercase px-2 py-0.5 rounded-md tracking-widest">
                              {t.partido}
                            </Badge>
                          )}
                          <span className="text-[9px] text-text-muted font-mono opacity-60">
                            #{t.id.substring(0, 6)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5">
                      <div 
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-bg-main border border-border-main rounded-2xl shadow-inner group-hover:border-brand-primary/30 transition-colors"
                      >
                        <div 
                          className="w-2 h-2 rounded-full animate-pulse" 
                          style={{ backgroundColor: t.color || '#333' }}
                        />
                        <span className="text-[10px] font-black uppercase tracking-widest" style={{ color: t.color || '#333' }}>
                          {t.nivel_risco}
                        </span>
                      </div>
                      {t.cargo && (
                        <div className="text-[8px] text-text-muted font-black uppercase tracking-tighter bg-bg-main/50 px-2 py-1 rounded-lg border border-border-main/50">
                          {t.cargo}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* KPIs Dashboard Grid */}
                  <div className="mt-6 grid grid-cols-3 gap-3 relative z-10">
                    <div className="bg-bg-main/40 p-3 rounded-2xl border border-border-main/50 group-hover:bg-bg-main/60 transition-colors">
                      <div className="text-xl font-black text-text-main leading-none tabular-nums">{t.comentarios_odio_count}</div>
                      <div className="text-[8px] font-bold text-text-muted uppercase tracking-tighter mt-1.5">Alertas (24h)</div>
                    </div>
                    <div className="bg-brand-primary/5 p-3 rounded-2xl border border-brand-primary/10 group-hover:bg-brand-primary/10 transition-colors">
                      <div className="text-xl font-black text-brand-primary leading-none tabular-nums">{t.score_risco}%</div>
                      <div className="text-[8px] font-bold text-brand-primary uppercase tracking-tighter mt-1.5">Severidade</div>
                    </div>
                    <div className="bg-emerald-500/5 p-3 rounded-2xl border border-emerald-500/10 group-hover:bg-emerald-500/10 transition-colors">
                      <div className="text-xl font-black text-emerald-500 leading-none tabular-nums">{healthScore}%</div>
                      <div className="text-[8px] font-bold text-emerald-600 uppercase tracking-tighter mt-1.5">Saúde Cívica</div>
                    </div>
                  </div>

                  {/* Detalhamento PASA (Mini Charts) */}
                  {t.breakdown && Object.keys(t.breakdown).length > 0 && (
                    <div className="mt-5 space-y-2 relative z-10">
                      <div className="flex justify-between items-center px-1">
                        <span className="text-[8px] font-black text-text-muted uppercase tracking-[0.2em]">Padrões Detectados (MCA v2.2)</span>
                        <span className="text-[8px] font-mono text-text-muted opacity-60">v85.4 neural</span>
                      </div>
                      <div className="flex h-2 w-full bg-bg-main/80 rounded-full overflow-hidden border border-border-main/30 p-[1px]">
                        {Object.entries(t.breakdown).map(([cat, count], i) => (
                          <div 
                            key={cat}
                            className="h-full transition-all duration-1000 first:rounded-l-full last:rounded-r-full"
                            style={{ 
                              width: `${(count / totalHate) * 100}%`,
                              backgroundColor: i % 2 === 0 ? '#8b5cf6' : '#ef4444',
                              opacity: 1 - (i * 0.15)
                            }}
                          />
                        ))}
                      </div>
                      <div className="flex flex-wrap gap-x-3 gap-y-1 px-1">
                         {Object.entries(t.breakdown).slice(0, 3).map(([cat, count], i) => (
                           <div key={cat} className="flex items-center gap-1">
                              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: i % 2 === 0 ? '#8b5cf6' : '#ef4444' }} />
                              <span className="text-[7px] font-black text-text-muted uppercase tracking-tighter">{cat.split('_')[0]} ({count})</span>
                           </div>
                         ))}
                      </div>
                    </div>
                  )}

                  {/* Ação Interativa no Footer */}
                  <div className="mt-6 flex items-center justify-between pt-4 border-t border-border-main/50 relative z-10">
                    <div className="flex items-center gap-2">
                       <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                       <span className="text-[9px] font-bold text-text-muted uppercase tracking-widest">Sincronizado</span>
                    </div>
                    <div className="text-[9px] font-black text-brand-primary uppercase tracking-widest group-hover:translate-x-1 transition-transform flex items-center gap-1">
                      Acessar dossiê detalhado ➔
                    </div>
                  </div>

                  {/* Hover Accent Line */}
                  <div className="absolute inset-x-0 bottom-0 h-1.5 bg-gradient-to-r from-brand-primary via-brand-primary/50 to-brand-primary transform scale-x-0 group-hover:scale-x-100 transition-transform duration-700" />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer / Observer */}
      <div className="p-4 bg-bg-main/30 border-t border-border-main flex justify-between items-center text-[10px] font-mono text-text-muted uppercase tracking-widest">
        <div className="flex items-center gap-4">
           <span>Malha de Dados v85.5</span>
           <span className="opacity-40">•</span>
           <span>PASA Protocol Active</span>
        </div>
        <div ref={observerRef} className="flex items-center gap-2">
          {filteredTargets.length > visibleCount && <Loader2 className="w-3 h-3 animate-spin" />}
          Sincronizado via Supabase Realtime
        </div>
      </div>
    </div>
  );
}
