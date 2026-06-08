'use client';
import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Users, Filter, Plus, Loader2, Search, X } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import { useWallet } from '@/hooks/useWallet';
import Button from '@/components/Button';
export interface Target {
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

import TargetFilters from './targets/TargetFilters';
import TargetCard from './targets/TargetCard';

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
      const username = prompt("Digite o @ do Instagram do novo alvo (ex: jairbolsonaro):");
      if (!username) return;

      const cleanUsername = username.replace('@', '').trim().toLowerCase();

      const confirmAdd = window.confirm(`[BETA GRATUITO] Injetar @${cleanUsername} na malha neural para monitoramento 24/7? (Operação gratuita durante o stress test)`);
      if (!confirmAdd) return;

      try {
        setIsAdding(true);
        const userId = localStorage.getItem('sentinela_user_id') || 'guest';

        // PASA v94.1 - Centralização via API para Auditoria de Fraude
        await fetchApi('/api/v1/ci/consume', {
          method: 'POST',
          body: JSON.stringify({
            user_id: userId,
            amount: 0,
            type: 'CONSUMPTION',
            description: `Injeção de Alvo (Free Tier): @${cleanUsername}`
          })
        });

        await supabase.from('candidatos').insert({
          username: cleanUsername,
          estado: 'BR',
          status_monitoramento: 'Ativo'
        });

        refreshBalance();
        refetch();
        alert(`Alvo @${cleanUsername} injetado com sucesso na malha de coleta (Modo Gratuito).`);
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
          <Button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 border rounded-xl text-[10px] font-bold transition-all uppercase ${showFilters ? 'bg-brand-primary/10 border-brand-primary text-brand-primary' : 'bg-bg-card border-border-main text-text-main hover:bg-bg-main shadow-sm'}`}
          >
            <Filter className="w-3 h-3" />
            {showFilters ? 'Fechar Filtros' : 'Filtrar Alvos'}
          </Button>
          <Button
            onClick={handleAddTarget}
            disabled={isAdding}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-xl text-[10px] font-black hover:bg-brand-primary/90 transition-all uppercase shadow-lg shadow-brand-primary/20 disabled:opacity-50"
          >
            {isAdding ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
            Novo Alvo (500 CI)
          </Button>
        </div>
      </div>

      {/* Painel de Filtros Avançados */}
      {showFilters && (
        <TargetFilters
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          riskFilter={riskFilter}
          setRiskFilter={setRiskFilter}
          partyFilter={partyFilter}
          setPartyFilter={setPartyFilter}
          stateFilter={stateFilter}
          setStateFilter={setStateFilter}
          parties={parties}
          states={states}
          setVisibleCount={setVisibleCount}
        />
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
            {filteredTargets.slice(0, visibleCount).map((t) => (
              <TargetCard key={t.id} t={t} />
            ))}
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
