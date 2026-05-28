'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { 
  Activity, 
  TrendingUp, 
  Users, 
  Coins, 
  ArrowUpRight,
  ShieldCheck,
  Zap,
  BarChart3
} from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface AdminDashboardData {
  kpis: {
    total_purchased: number;
    total_spent: number;
    total_circulating: number;
    estimated_revenue_brl: number;
  };
  top_spenders: Array<{
    id: string;
    full_name: string;
    stn_tokens: number;
    total_stn_spent: number;
  }>;
  modules_breakdown: Record<string, number>;
  recent_transactions: Array<{
    id: string;
    type: string;
    amount: number;
    created_at: string;
    user_id: string;
    metadata: any;
  }>;
}

export default function AdminFinanceiroPage() {
  const { data, isLoading, isError } = useQuery<AdminDashboardData>({
    queryKey: ['admin-finance-dashboard'],
    queryFn: async () => {
      return await fetchApi('/api/v1/admin/finance/dashboard');
    },
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-4 border-brand-primary border-t-transparent animate-spin" />
          <p className="text-text-muted font-mono uppercase tracking-widest text-xs animate-pulse">Sincronizando Malha Financeira...</p>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex h-[80vh] items-center justify-center text-red-500 font-mono text-sm">
        Falha ao conectar com o terminal seguro (GOD Mode).
      </div>
    );
  }

  const { kpis, top_spenders, modules_breakdown, recent_transactions } = data;

  // Calculate percentages for modules breakdown
  const totalBreakdown = Object.values(modules_breakdown).reduce((a, b) => a + b, 0);

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-bg-card border border-border-main rounded-2xl shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge className="bg-brand-primary/10 text-brand-primary border-brand-primary/20 text-[10px] font-black uppercase tracking-widest rounded-sm">
              GOD MODE
            </Badge>
            <span className="text-[10px] font-mono text-text-muted uppercase">Terminal Administrativo</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-black text-text-main tracking-tight flex items-center gap-2">
            <Activity className="w-6 h-6 text-brand-primary" />
            Operações e Faturamento
          </h1>
          <p className="text-sm text-text-muted font-medium mt-1">
            Mapeamento em tempo real do ecossistema de Inteligência.
          </p>
        </div>
        <div className="flex items-center gap-4 bg-bg-main p-4 rounded-xl border border-border-main">
          <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1">Receita Estimada (BRL)</p>
            <p className="text-2xl font-black text-text-main font-mono">
              R$ {kpis.estimated_revenue_brl.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* KPIs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm flex items-start gap-4">
          <div className="w-12 h-12 bg-brand-primary/10 rounded-xl flex items-center justify-center shrink-0">
            <Coins className="w-6 h-6 text-brand-primary" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1">Tokens Minerados (Lifetime)</p>
            <p className="text-3xl font-black text-text-main font-mono">{kpis.total_purchased.toLocaleString()}</p>
            <p className="text-xs text-text-muted mt-1">Total de CI já gerados no sistema.</p>
          </div>
        </div>

        <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm flex items-start gap-4">
          <div className="w-12 h-12 bg-orange-500/10 rounded-xl flex items-center justify-center shrink-0">
            <Zap className="w-6 h-6 text-orange-500" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1">Tokens Queimados (Consumo)</p>
            <p className="text-3xl font-black text-text-main font-mono">{kpis.total_spent.toLocaleString()}</p>
            <p className="text-xs text-text-muted mt-1">CIs já consumidos nas catracas.</p>
          </div>
        </div>

        <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm flex items-start gap-4">
          <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1">Tokens em Circulação (Float)</p>
            <p className="text-3xl font-black text-text-main font-mono">{kpis.total_circulating.toLocaleString()}</p>
            <p className="text-xs text-text-muted mt-1">CIs parados nas carteiras ativas.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Module Breakdown */}
        <div className="lg:col-span-1 bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-border-main bg-bg-main/50 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-primary" />
            <h3 className="font-black text-text-main">Queima por Módulo</h3>
          </div>
          <div className="p-6 flex-1 flex flex-col justify-center space-y-6">
            {Object.entries(modules_breakdown).map(([module, amount]) => {
              const percent = totalBreakdown > 0 ? (amount / totalBreakdown) * 100 : 0;
              return (
                <div key={module}>
                  <div className="flex justify-between text-xs font-bold text-text-main mb-2">
                    <span className="uppercase">{module}</span>
                    <span className="font-mono text-brand-primary">{amount.toLocaleString()} CI</span>
                  </div>
                  <div className="w-full bg-bg-main rounded-full h-2 overflow-hidden border border-border-main">
                    <div 
                      className="bg-brand-primary h-2 transition-all duration-1000" 
                      style={{ width: `${percent}%` }} 
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Spenders & Recent */}
        <div className="lg:col-span-2 space-y-6 flex flex-col">
          {/* Top Spenders */}
          <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-border-main bg-bg-main/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-primary" />
                <h3 className="font-black text-text-main">Maiores Operadores (Top Spenders)</h3>
              </div>
            </div>
            <Table>
              <TableHeader className="bg-bg-main/30">
                <TableRow className="border-border-main">
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Usuário</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted text-right">Saldo Atual (CI)</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted text-right">Total Gasto (CI)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {top_spenders.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="text-center py-8 text-xs text-text-muted font-mono">
                      Nenhuma carteira localizada.
                    </TableCell>
                  </TableRow>
                ) : top_spenders.map((user) => (
                  <TableRow key={user.id} className="border-border-main hover:bg-bg-main/50">
                    <TableCell className="font-medium text-xs text-text-main">
                      {user.full_name || user.id.split('-')[0]}
                      <span className="block text-[10px] text-text-muted font-mono mt-0.5">{user.id}</span>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-bold text-emerald-500">
                      {user.stn_tokens?.toLocaleString() || 0}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-black text-brand-primary">
                      {user.total_stn_spent?.toLocaleString() || 0}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Recent Transactions */}
          <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden flex-1">
            <div className="p-6 border-b border-border-main bg-bg-main/50 flex items-center gap-2">
              <ArrowUpRight className="w-5 h-5 text-brand-primary" />
              <h3 className="font-black text-text-main">Últimas Transações Globais</h3>
            </div>
            <Table>
              <TableHeader className="bg-bg-main/30">
                <TableRow className="border-border-main">
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Data</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Tipo</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Operação</TableHead>
                  <TableHead className="text-[10px] font-bold uppercase tracking-wider text-text-muted text-right">Valor (CI)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recent_transactions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-xs text-text-muted font-mono">
                      Nenhuma transação na rede.
                    </TableCell>
                  </TableRow>
                ) : recent_transactions.map((tx) => (
                  <TableRow key={tx.id} className="border-border-main hover:bg-bg-main/50">
                    <TableCell className="text-[10px] text-text-muted font-mono">
                      {new Date(tx.created_at).toLocaleString('pt-BR')}
                    </TableCell>
                    <TableCell>
                      <Badge className={`text-[9px] font-black uppercase rounded shadow-none ${
                        tx.type === 'PURCHASE' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 
                        tx.type === 'CONSUMPTION' ? 'bg-orange-500/10 text-orange-500 border border-orange-500/20' : 
                        'bg-brand-primary/10 text-brand-primary border border-brand-primary/20'
                      }`}>
                        {tx.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-text-main font-medium">
                      {tx.metadata?.action ? String(tx.metadata.action).replace('unlock_', 'Desbloqueio: ').replace('add_', 'Inclusão: ') : 'Aporte Stripe'}
                    </TableCell>
                    <TableCell className={`text-right font-mono text-xs font-black ${tx.amount > 0 ? 'text-emerald-500' : 'text-orange-500'}`}>
                      {tx.amount > 0 ? '+' : ''}{tx.amount}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
}
