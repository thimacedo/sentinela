'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Users, Filter } from 'lucide-react';

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
}

export default function TargetsTab() {
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');

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

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
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

      <Table>
        <TableHeader className="bg-bg-main/30">
          <TableRow className="border-border-main hover:bg-transparent">
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Identificação</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Nível de Risco</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Alertas de Ódio</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-right px-6">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
                SINCRONIZANDO COM O OBSERVATÓRIO...
              </TableCell>
            </TableRow>
          ) : filteredTargets.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted font-mono text-xs">
                NENHUM ALVO ATIVO COM OS FILTROS SELECIONADOS.
              </TableCell>
            </TableRow>
          ) : (
            filteredTargets.map((t) => (
              <TableRow key={t.id} className="border-border-main hover:bg-bg-main/50 transition-colors">
                <TableCell className="px-6 py-4">
                  <div className="font-black text-text-main text-sm font-mono tracking-tight">@{t.username}</div>
                  <div className="text-[10px] text-text-muted font-medium mt-0.5 uppercase tracking-tighter">
                    ID: {t.id.substring(0, 8)}
                  </div>
                </TableCell>
                <TableCell className="text-center">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-bg-main border border-border-main rounded-full">
                    <div 
                      className="w-1.5 h-1.5 rounded-full animate-pulse shadow-sm" 
                      style={{ backgroundColor: t.color || '#333' }}
                    />
                    <span className="text-[10px] font-black uppercase tracking-wider" style={{ color: t.color || '#333' }}>
                      {t.nivel_risco}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-center">
                  <div className="font-black text-text-main text-lg">{t.comentarios_odio_count}</div>
                </TableCell>
                <TableCell className="text-right px-6 py-4">
                  <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-md shadow-none text-[9px] font-black uppercase">
                    {t.status_monitoramento}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      <div className="p-4 bg-bg-main/30 border-t border-border-main text-center text-xs text-text-muted">
        Total de {filteredTargets.length} perfis exibidos de {targets.length} monitorados.
      </div>
    </div>
  );
}
