import React from 'react';
import { Search, X } from 'lucide-react';
import Button from '@/components/Button';

interface TargetFiltersProps {
  searchQuery: string;
  setSearchQuery: (val: string) => void;
  riskFilter: string;
  setRiskFilter: (val: string) => void;
  partyFilter: string;
  setPartyFilter: (val: string) => void;
  stateFilter: string;
  setStateFilter: (val: string) => void;
  parties: string[];
  states: string[];
  setVisibleCount: (val: number) => void;
}

export default function TargetFilters({
  searchQuery, setSearchQuery,
  riskFilter, setRiskFilter,
  partyFilter, setPartyFilter,
  stateFilter, setStateFilter,
  parties, states,
  setVisibleCount
}: TargetFiltersProps) {
  return (
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
        <Button
          onClick={() => {
            setSearchQuery('');
            setRiskFilter('ALL');
            setPartyFilter('ALL');
            setStateFilter('ALL');
          }}
          className="sm:col-span-full md:col-span-4 text-[9px] font-black text-red-500 hover:text-red-600 transition-colors uppercase tracking-widest flex items-center justify-center gap-1 mt-2"
        >
          <X className="w-3 h-3" /> Limpar Filtros Avançados
        </Button>
      )}
    </div>
  );
}
