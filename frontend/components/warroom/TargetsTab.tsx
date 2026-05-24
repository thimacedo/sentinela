'use client';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

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
  const { data: targets = [], isLoading } = useQuery<Target[]>({
    queryKey: ['active-targets-enriched'],
    queryFn: async () => {
      return await fetchApi('/api/v1/targets');
    },
    refetchInterval: 60000,
  });

  return (
    <Card className="p-4 bg-black/50 border-tactical-accent">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-tactical-accent uppercase tracking-wider">Radar de Alvos</h2>
        <span className="text-xs text-gray-500 font-mono">ORDENADO POR SEVERIDADE</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="border-tactical-accent/30 hover:bg-transparent">
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Username</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Nível de Risco</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Alertas</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                SINCRONIZANDO COM A REDE...
              </TableCell>
            </TableRow>
          ) : targets.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 font-mono">
                NENHUM ALVO ATIVO NO RADAR.
              </TableCell>
            </TableRow>
          ) : (
            targets.map((t) => (
              <TableRow key={t.id} className="border-tactical-accent/10 hover:bg-tactical-accent/5 transition-colors">
                <TableCell className="font-bold text-gray-200">@{t.username}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-2 h-2 rounded-full animate-pulse" 
                      style={{ backgroundColor: t.color || '#333' }}
                    />
                    <span className="text-[10px] uppercase font-bold" style={{ color: t.color || '#333' }}>
                      {t.nivel_risco}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-center font-mono text-sm text-tactical-accent">
                  {t.comentarios_odio_count}
                </TableCell>
                <TableCell className="text-right">
                  <Badge className="bg-tactical-accent text-black hover:bg-tactical-accent/80 border-none rounded-none text-[10px] font-bold">
                    {t.status_monitoramento}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}
