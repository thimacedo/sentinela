'use client';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import React, { useState } from 'react';

import { fetchApi, postCommand } from '@/lib/api';

interface Worker {
  worker: string;
  status: string;
  total_executions: number;
  success_rate: number;
  avg_duration_ms: number;
  avg_throughput_items_per_sec: number;
  total_items_processed: number;
  last_run_at: string;
}

interface Telemetry {
  total_workers: number;
  healthy_workers: number;
  system_health: string;
  total_executions: number;
  total_items_processed: number;
  workers: Worker[];
}

export default function QueueTab() {
  const [paused, setPaused] = useState(false);
  const togglePause = async () => {
    try {
      await postCommand(paused ? 'RESUME' : 'PAUSE');
      setPaused(!paused);
    } catch (e) {
      console.error('Failed to send pause command:', e);
    }
  };
  const { data, isLoading } = useQuery<Telemetry>({
    queryKey: ['workers-telemetry'],
    queryFn: async () => {
      return await fetchApi('/api/v1/monitor/workers');
    },
    refetchInterval: 10000, // Telemetria rápida (10s)
    enabled: !paused,
  });

  const getStatusColor = (status: string) => {
    return status === 'healthy' ? 'bg-tactical-accent' : 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-text-main">Telemetria Workers</h3>
        <button
          onClick={togglePause}
          className="flex items-center gap-2 px-3 py-1.5 bg-bg-card border border-border-main rounded-full text-xs font-bold uppercase hover:bg-bg-main transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"></path></svg>
          {paused ? 'Retomar' : 'Pausar'}
        </button>
      </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-min">
        <Card className="p-4 bg-black/50 border-tactical-accent flex flex-col justify-between">
          <h3 className="text-xs text-gray-500 uppercase mb-2">Saúde do Sistema</h3>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full animate-ping ${data?.system_health === 'green' ? 'bg-tactical-accent' : 'bg-red-500'}`} />
            <span className="text-2xl font-bold uppercase">{data?.system_health || '---'}</span>
          </div>
        </Card>
        <Card className="p-4 bg-black/50 border-tactical-accent flex flex-col justify-between">
          <h3 className="text-xs text-gray-500 uppercase mb-2">Workers Ativos</h3>
          <div className="text-2xl font-bold">{data?.healthy_workers || 0} / {data?.total_workers || 0}</div>
        </Card>
        <Card className="p-4 bg-black/50 border-tactical-accent flex flex-col justify-between">
          <h3 className="text-xs text-gray-500 uppercase mb-2">Vazão Global</h3>
          <div className="text-2xl font-bold text-tactical-accent">
            {data?.workers.reduce((acc, w) => acc + w.avg_throughput_items_per_sec, 0).toFixed(2) || "0.00"} <span className="text-xs text-gray-500">items/s</span>
          </div>
        </Card>
      </div>

      <Card className="p-4 bg-black/50 border-tactical-accent overflow-x-auto overflow-y-auto max-h-96 md:col-span-3">
        <h2 className="text-xl font-bold mb-4 text-tactical-accent uppercase tracking-wider">Status dos Workers</h2>
        <Table>
          <TableHeader>
            <TableRow className="border-tactical-accent/30 hover:bg-transparent">
              <TableHead className="text-tactical-accent/70 uppercase text-xs">Worker</TableHead>
              <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Status</TableHead>
              <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Taxa Sucesso</TableHead>
              <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Vazão</TableHead>
              <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Total Processado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                  INTERCEPTANDO TELEMETRIA...
                </TableCell>
              </TableRow>
            ) : data?.workers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500 font-mono">
                  NENHUM WORKER EM OPERAÇÃO.
                </TableCell>
              </TableRow>
            ) : (
              data?.workers.map((w) => (
                <TableRow key={w.worker} className="border-tactical-accent/10 hover:bg-tactical-accent/5">
                  <TableCell className="font-mono text-xs font-bold">{w.worker}</TableCell>
                  <TableCell className="text-center">
                    <Badge className={`${getStatusColor(w.status)} text-black text-[9px] rounded-none uppercase font-bold`}>
                      {w.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center font-mono text-xs">
                    {w.success_rate}%
                  </TableCell>
                  <TableCell className="text-center font-mono text-xs text-tactical-accent">
                    {w.avg_throughput_items_per_sec} items/s
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {w.total_items_processed.toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
