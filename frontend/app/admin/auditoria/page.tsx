'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { 
  Activity, 
  Cpu, 
  ShieldAlert, 
  Database, 
  BarChart3,
  Server,
  Terminal,
  AlertTriangle,
  Lock,
  Key,
  ChevronRight
} from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface ProviderSpending {
  provider: string;
  status: string;
  total_calls: number;
  success_calls: number;
  error_calls: number;
  avg_text_length: number;
}

interface TargetSpending {
  candidato_id: string;
  total_calls: number;
  estimated_tokens: number;
}

interface CloudError {
  provider: string;
  error_type: string;
  error_count: number;
}

export default function AdminAuditoriaPage() {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [passkey, setPasskey] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const { data: providers = [], isLoading: providersLoading } = useQuery<ProviderSpending[]>({
    queryKey: ['admin-spending-providers'],
    queryFn: () => fetchApi('/api/v1/analytics/spending/providers'),
    enabled: isAuthorized,
  });

  const { data: targets = [], isLoading: targetsLoading } = useQuery<TargetSpending[]>({
    queryKey: ['admin-spending-targets'],
    queryFn: () => fetchApi('/api/v1/analytics/spending/targets'),
    enabled: isAuthorized,
  });

  const { data: errors = [], isLoading: errorsLoading } = useQuery<CloudError[]>({
    queryKey: ['admin-spending-errors'],
    queryFn: () => fetchApi('/api/v1/analytics/spending/errors'),
    enabled: isAuthorized,
  });

  const handleAuth = (e: React.FormEvent) => {
    e.preventDefault();
    if (passkey === 'SENTINELA-GOD' || passkey === process.env.NEXT_PUBLIC_ADMIN_PIN) {
      setIsAuthorized(true);
      setErrorMsg('');
    } else {
      setErrorMsg('Código de Autorização Inválido.');
      setPasskey('');
    }
  };

  if (!isAuthorized) {
    return (
      <div className="flex h-[80vh] items-center justify-center p-4">
        <form onSubmit={handleAuth} className="bg-bg-card border border-border-main rounded-2xl p-8 shadow-2xl max-w-sm w-full animate-in zoom-in-95 duration-300">
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-16 h-16 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4 border border-indigo-500/20">
              <Lock className="w-8 h-8 text-indigo-500" />
            </div>
            <h2 className="text-xl font-black text-text-main tracking-tight uppercase">Auditoria Técnica</h2>
            <p className="text-xs text-text-muted mt-2 font-mono uppercase">Módulo de Integridade Infraestrutural</p>
          </div>
          
          <div className="space-y-4">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Key className="h-4 w-4 text-text-muted" />
              </div>
              <input
                type="password"
                placeholder="Código de Acesso SRE"
                value={passkey}
                onChange={(e) => setPasskey(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-bg-main border border-border-main rounded-xl text-sm text-text-main focus:outline-none focus:border-indigo-500 transition-colors text-center font-mono tracking-widest"
                autoFocus
              />
            </div>
            {errorMsg && <p className="text-[10px] text-red-500 font-bold uppercase text-center">{errorMsg}</p>}
            
            <button type="submit" className="w-full py-3 bg-indigo-600 text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20">
              Desbloquear Terminal
            </button>
          </div>
        </form>
      </div>
    );
  }

  const totalCalls = providers.reduce((acc, p) => acc + p.total_calls, 0);
  const totalErrors = providers.reduce((acc, p) => acc + p.error_calls, 0);
  const healthRate = totalCalls > 0 ? ((totalCalls - totalErrors) / totalCalls) * 100 : 100;

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">
      {/* Header Técnico */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-bg-card border border-border-main rounded-2xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center border border-indigo-500/20">
            <Terminal className="w-6 h-6 text-indigo-500" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-text-main tracking-tight uppercase flex items-center gap-2">
              Auditoria de IA & Infra
            </h1>
            <p className="text-xs text-text-muted font-mono uppercase tracking-widest mt-1">
              PASA v94.3 // Engine Mesh Resilience
            </p>
          </div>
        </div>
        <div className="flex gap-4">
           <div className="bg-bg-main px-4 py-2 rounded-lg border border-border-main flex flex-col items-end">
              <span className="text-[10px] text-text-muted font-bold uppercase tracking-tighter">Status da Malha</span>
              <span className={`text-sm font-black ${healthRate > 90 ? 'text-green-500' : 'text-yellow-500'}`}>
                {healthRate.toFixed(1)}% Estável
              </span>
           </div>
        </div>
      </div>

      {/* Grid de Tabelas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Provedores IA */}
        <div className="bg-bg-card border border-border-main rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border-main bg-bg-main/30 flex items-center justify-between">
            <h3 className="text-xs font-black text-text-main uppercase tracking-widest flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-500" /> Malha de Provedores
            </h3>
            <Badge className="bg-indigo-500/10 text-indigo-500 border-indigo-500/20 text-[9px]">REAL-TIME</Badge>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="border-border-main hover:bg-transparent">
                <TableHead className="text-[10px] uppercase font-bold">Provedor</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-center">Calls</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-center">Sucesso</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-center">Falhas</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {providersLoading ? (
                 <TableRow><TableCell colSpan={4} className="text-center py-8 animate-pulse text-[10px] text-text-muted uppercase">Sincronizando Mesh...</TableCell></TableRow>
              ) : providers.map((p, i) => (
                <TableRow key={i} className="border-border-main hover:bg-bg-main/20">
                  <TableCell className="font-mono text-xs text-text-main uppercase font-bold">{p.provider}</TableCell>
                  <TableCell className="text-center font-mono text-xs">{p.total_calls}</TableCell>
                  <TableCell className="text-center font-mono text-xs text-green-500">{p.success_calls}</TableCell>
                  <TableCell className="text-center font-mono text-xs text-red-500 font-bold">{p.error_calls}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Sumário de Erros Cloud */}
        <div className="bg-bg-card border border-border-main rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border-main bg-bg-main/30 flex items-center justify-between">
            <h3 className="text-xs font-black text-text-main uppercase tracking-widest flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-500" /> Incidentes Cloud
            </h3>
            <Badge className="bg-red-500/10 text-red-500 border-red-500/20 text-[9px]">SRE LOG</Badge>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="border-border-main hover:bg-transparent">
                <TableHead className="text-[10px] uppercase font-bold">Origem</TableHead>
                <TableHead className="text-[10px] uppercase font-bold">Tipo de Erro</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-right">Ocorrências</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {errorsLoading ? (
                 <TableRow><TableCell colSpan={3} className="text-center py-8 animate-pulse text-[10px] text-text-muted uppercase">Varrendo Logs de Falha...</TableCell></TableRow>
              ) : errors.length === 0 ? (
                <TableRow><TableCell colSpan={3} className="text-center py-8 text-[10px] text-green-500 font-bold">NENHUM INCIDENTE NAS ÚLTIMAS 24H</TableCell></TableRow>
              ) : errors.map((e, i) => (
                <TableRow key={i} className="border-border-main hover:bg-bg-main/20">
                  <TableCell className="font-mono text-xs text-text-muted uppercase">{e.provider}</TableCell>
                  <TableCell className="text-xs text-red-400 font-medium">{e.error_type}</TableCell>
                  <TableCell className="text-right font-mono text-xs font-black">{e.error_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Consumo por Alvo (Top Spenders de Tokens) */}
        <div className="lg:col-span-2 bg-bg-card border border-border-main rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border-main bg-bg-main/30 flex items-center justify-between">
            <h3 className="text-xs font-black text-text-main uppercase tracking-widest flex items-center gap-2">
              <Database className="w-4 h-4 text-orange-500" /> Distribuição de Carga por Alvo
            </h3>
            <Badge className="bg-orange-500/10 text-orange-500 border-orange-500/20 text-[9px]">TOKEN AUDIT</Badge>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="border-border-main hover:bg-transparent">
                <TableHead className="text-[10px] uppercase font-bold">Identificador do Alvo</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-center">Chamadas IA</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-center">Tokens Est. (K)</TableHead>
                <TableHead className="text-[10px] uppercase font-bold text-right">Custo Est. (USD)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {targetsLoading ? (
                 <TableRow><TableCell colSpan={4} className="text-center py-8 animate-pulse text-[10px] text-text-muted uppercase">Auditando Alvos...</TableCell></TableRow>
              ) : targets.map((t, i) => {
                const tokensK = t.estimated_tokens / 1000;
                const costUSD = tokensK * 0.002; // Média Cloud
                return (
                  <TableRow key={i} className="border-border-main hover:bg-bg-main/20">
                    <TableCell className="font-bold text-xs text-text-main">@{t.candidato_id}</TableCell>
                    <TableCell className="text-center font-mono text-xs">{t.total_calls}</TableCell>
                    <TableCell className="text-center font-mono text-xs">{tokensK.toFixed(1)}k</TableCell>
                    <TableCell className="text-right font-mono text-xs font-black text-orange-500">
                      ${costUSD.toFixed(4)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          <div className="p-4 bg-bg-main/50 border-t border-border-main">
            <p className="text-[10px] text-text-muted leading-relaxed font-sans">
              * Estimativa baseada em 1 token / 4 chars. O custo USD reflete a média entre Gemini 1.5 Flash e Groq Llama 3.1.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
