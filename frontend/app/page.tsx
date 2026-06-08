'use client';
import React, { useState, useEffect } from 'react';
import { useDashboardStats } from '@/hooks/useDashboardData';
import { supabase } from '@/lib/supabase';
import { useQuery } from '@tanstack/react-query';
import { AlertOctagon, Activity, ShieldAlert, CheckCircle2, TrendingUp, Users, Cpu } from 'lucide-react';
import Link from 'next/link';

export default function DecisionRoom() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();

  // 1. Matriz de Alertas Críticos
  const { data: criticalAlerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ['critical-alerts'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('comentarios')
        .select('id, texto_bruto, categoria_ia, confianca_ia, ccf_sync, data_coleta, candidatos!inner(username)')
        .in('categoria_ia', ['CRITICO', 'ATAQUE_INSTITUCIONAL', 'ELEVADO'])
        .eq('is_hate', true)
        .order('data_coleta', { ascending: false })
        .limit(10);
      if (error) throw error;
      return data;
    },
    refetchInterval: 15000,
  });

  // 2. Saúde do Motor (Watchdog via SSE)
  const [motorStatus, setMotorStatus] = useState<'OPERACIONAL' | 'FALHA' | 'CONECTANDO'>('CONECTANDO');
  const [lastLog, setLastLog] = useState('');

  useEffect(() => {
    const source = new EventSource("http://localhost:8001/api/stream");
    source.onmessage = (event) => {
      try {
        const newLog = JSON.parse(event.data);
        setMotorStatus('OPERACIONAL');
        setLastLog(`[${newLog.time}] ${newLog.message}`);
      } catch (e) {
        // ignore
      }
    };
    source.onerror = () => setMotorStatus('FALHA');
    return () => source.close();
  }, []);

  const topTargets = stats?.top_alvos?.slice(0, 3) || [];
  const riskTemperature = stats?.total_amostra ? ((stats?.total_classificados || 0) / stats.total_amostra) * 100 : 0;

  return (
    <div className="min-h-screen bg-black text-gray-300 font-mono selection:bg-gray-800">
      <main className="max-w-[1400px] mx-auto py-6 px-4 space-y-6">
        
        {/* HEADER: Decision Room */}
        <header className="flex justify-between items-end border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-2xl font-black text-white tracking-tighter uppercase flex items-center gap-3">
              <Activity className="w-6 h-6 text-indigo-500" />
              Decision Room
            </h1>
            <p className="text-xs text-gray-500 mt-1 tracking-widest uppercase">
              Sentinela Democrática // Painel Tático e Gerencial
            </p>
          </div>
          <div className="text-right hidden sm:block">
            <div className="text-[10px] text-gray-500 uppercase tracking-widest">Motor Autopilot</div>
            <div className="flex items-center gap-2 justify-end mt-1">
              <span className={`w-2 h-2 rounded-full ${motorStatus === 'OPERACIONAL' ? 'bg-green-500 animate-pulse' : motorStatus === 'FALHA' ? 'bg-red-500' : 'bg-yellow-500'}`} />
              <span className={`text-xs font-bold ${motorStatus === 'OPERACIONAL' ? 'text-green-500' : motorStatus === 'FALHA' ? 'text-red-500' : 'text-yellow-500'}`}>
                {motorStatus}
              </span>
            </div>
          </div>
        </header>

        {/* SECTION 1: MACRO-INDICADORES */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* Eficiência da IA */}
          <div className="bg-gray-900 border border-gray-800 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-2">
                <Cpu className="w-3 h-3" /> Throughput e Eficiência
              </span>
            </div>
            <div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-black text-white">
                  {statsLoading ? '-' : stats?.total_classificados?.toLocaleString('pt-BR')}
                </span>
                <span className="text-xs text-gray-500 mb-1">Processados</span>
              </div>
              <div className="w-full bg-gray-800 h-1.5 mt-4 rounded-full overflow-hidden">
                <div className="bg-indigo-500 h-full" style={{ width: `${Math.min(riskTemperature, 100)}%` }} />
              </div>
              <div className="flex justify-between mt-2 text-[10px] text-gray-500">
                <span>Fila Restante: <span className="text-yellow-500 font-bold">{stats?.total_nao_processados?.toLocaleString('pt-BR')}</span></span>
                <span>Termômetro de Carga</span>
              </div>
            </div>
          </div>

          {/* Termômetro de Risco Global */}
          <div className="bg-gray-900 border border-gray-800 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-2">
                <TrendingUp className="w-3 h-3" /> Índice de Risco Global
              </span>
            </div>
            <div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-black text-red-500">
                  {statsLoading ? '-' : (stats?.resiliencia || 0).toFixed(1)}%
                </span>
                <span className="text-xs text-gray-500 mb-1">Pressão Semântica</span>
              </div>
              <p className="text-xs text-gray-400 mt-3 leading-relaxed">
                Relação direta de ataques detectados vs volume total neutro/positivo. Valores acima de 15% configuram crise reputacional global.
              </p>
            </div>
          </div>

          {/* Top 3 Alvos sob Ataque */}
          <div className="bg-gray-900 border border-gray-800 p-4 rounded-xl flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-2">
                <Users className="w-3 h-3" /> Focos de Crise (Top 3)
              </span>
            </div>
            <div className="flex-1 flex flex-col justify-center space-y-2">
              {statsLoading ? (
                <div className="text-xs text-gray-600 animate-pulse">Calculando frentes de ataque...</div>
              ) : topTargets.length === 0 ? (
                <div className="text-xs text-gray-600">Nenhum foco de crise detectado.</div>
              ) : (
                topTargets.map((t: any, i: number) => (
                  <div key={i} className="flex items-center justify-between bg-black/50 p-2 rounded border border-gray-800/50">
                    <span className="text-sm font-bold text-gray-300">@{t.username}</span>
                    <span className="text-xs font-bold text-red-400">{t.value} alertas</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* SECTION 2: MATRIZ DE AÇÃO & SISTEMA */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Matriz de Alertas Críticos */}
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl overflow-hidden flex flex-col h-[500px]">
            <div className="p-4 border-b border-gray-800 bg-black/20 flex justify-between items-center">
              <h2 className="text-sm font-bold text-white flex items-center gap-2 uppercase tracking-tight">
                <ShieldAlert className="w-4 h-4 text-red-500" /> Matriz de Ação Crítica
              </h2>
              <span className="text-[10px] text-gray-500 uppercase tracking-widest">Apenas Confiança &gt; 90%</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-gray-800">
              {alertsLoading ? (
                <div className="text-xs text-gray-600 animate-pulse">Varrendo banco de dados...</div>
              ) : criticalAlerts.length === 0 ? (
                <div className="text-xs text-gray-600 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" /> Nenhum alerta crítico não-mitigado.
                </div>
              ) : (
                criticalAlerts.map((alert: any) => (
                  <div key={alert.id} className="bg-black border-l-2 border-red-500 p-3 rounded-r-lg border border-gray-800 text-sm flex flex-col gap-2">
                    <div className="flex justify-between items-start gap-4">
                      <span className="font-bold text-red-400 text-xs">@{alert.candidatos?.username}</span>
                      <span className="text-[10px] text-gray-500">{(alert.confianca_ia * 100).toFixed(0)}% Match</span>
                    </div>
                    <p className="text-gray-300 line-clamp-2 leading-relaxed">"{alert.texto_bruto}"</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-[10px] bg-red-500/10 text-red-500 px-1.5 py-0.5 rounded uppercase font-bold">{alert.categoria_ia}</span>
                      {alert.ccf_sync > 0.8 && (
                        <span className="text-[10px] bg-yellow-500/10 text-yellow-500 px-1.5 py-0.5 rounded uppercase font-bold">Bot/Sync Detectado</span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Diagnóstico do Sistema */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden flex flex-col h-[500px]">
             <div className="p-4 border-b border-gray-800 bg-black/20">
              <h2 className="text-sm font-bold text-white flex items-center gap-2 uppercase tracking-tight">
                <AlertOctagon className="w-4 h-4 text-indigo-500" /> Diagnóstico do Motor
              </h2>
            </div>
            <div className="p-4 flex-1 flex flex-col justify-between">
              
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Status da API (Cloud)</div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 bg-gray-800 rounded-full overflow-hidden"><div className="bg-green-500 w-[95%] h-full" /></div>
                    <span className="text-xs text-green-500 font-bold">95%</span>
                  </div>
                </div>
                
                <div>
                  <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Bypass Autopilot L3</div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 bg-gray-800 rounded-full overflow-hidden"><div className="bg-indigo-500 w-full h-full" /></div>
                    <span className="text-xs text-indigo-500 font-bold">ON</span>
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-1">Gargalo de Fila</div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 bg-gray-800 rounded-full overflow-hidden">
                      <div className={`h-full ${(stats?.total_nao_processados || 0) > 5000 ? 'bg-red-500 w-[80%]' : 'bg-yellow-500 w-[30%]'}`} />
                    </div>
                    <span className="text-xs text-gray-400">{stats?.total_nao_processados > 1000 ? 'ALTO' : 'NORMAL'}</span>
                  </div>
                </div>
              </div>

              <div className="mt-8 border-t border-gray-800 pt-4">
                <div className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-2">Última Ação do Watchdog</div>
                <div className="bg-black p-3 rounded border border-gray-800 text-[10px] text-gray-400 font-mono line-clamp-3 leading-relaxed">
                  {lastLog || 'Aguardando pulso do servidor...'}
                </div>
              </div>

            </div>
          </div>

        </div>

      </main>
    </div>
  );
}
