'use client';
import { useQuery } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Share2, Globe } from 'lucide-react';

import { fetchApi } from '@/lib/api';

interface Network {
  id: string;
  nome_rede: string;
  total_perfis: number;
  data_deteccao: string;
  severidade: string;
}

export default function NetworkTab() {
  const { data: networks = [], isLoading } = useQuery<Network[]>({
    queryKey: ['networks-clusters'],
    queryFn: async () => {
      return await fetchApi('/api/v1/networks');
    },
    refetchInterval: 60000,
  });

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <Globe className="w-5 h-5 text-brand-primary" />
            Tendências e Redes Coordenadas
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Mapeamento de Influência e Narrativas</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-full">
          <Share2 className="w-3.5 h-3.5 text-brand-primary" />
          <span className="text-[10px] font-bold text-brand-primary uppercase">Módulo Solenya v71.0</span>
        </div>
      </div>

      <Table>
        <TableHeader className="bg-bg-main/30">
          <TableRow className="border-border-main hover:bg-transparent">
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Identificação do Cluster</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Perfis Suspeitos</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Detecção</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-right px-6">Nível de Risco</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
                MAPEANDO CONEXÕES OCULTAS...
              </TableCell>
            </TableRow>
          ) : networks.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted font-mono text-xs">
                NENHUMA REDE COORDENADA DETECTADA NO RADAR.
              </TableCell>
            </TableRow>
          ) : (
            networks.map((n) => (
              <TableRow key={n.id} className="border-border-main hover:bg-bg-main/50 transition-colors">
                <TableCell className="px-6 py-4">
                  <div className="font-black text-text-main text-sm uppercase tracking-tighter">
                    {n.nome_rede || `Cluster #${n.id.substring(0, 8)}`}
                  </div>
                </TableCell>
                <TableCell className="text-center font-black text-brand-primary">
                  {n.total_perfis}
                </TableCell>
                <TableCell className="text-center py-4 text-[10px] font-mono text-text-muted uppercase">
                  {n.data_deteccao ? new Date(n.data_deteccao).toLocaleDateString('pt-BR') : 'N/A'}
                </TableCell>
                <TableCell className="text-right px-6 py-4">
                  <Badge className="bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 text-[9px] font-black uppercase rounded-md shadow-none">
                    {n.severidade || 'MODERADO'}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      <div className="p-4 bg-bg-main/30 border-t border-border-main text-center text-[10px] text-text-muted uppercase tracking-widest font-medium">
        Algoritmo de Detecção de Padrões Coordenados Ativo
      </div>
    </div>
  );
}
