'use client';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Share2 } from 'lucide-react';

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
      const response = await fetch('/api/v1/networks');
      if (!response.ok) throw new Error('Falha ao buscar redes');
      return await response.json();
    },
    refetchInterval: 60000,
  });

  return (
    <Card className="p-4 bg-black/50 border-tactical-accent">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-tactical-accent uppercase tracking-wider flex items-center gap-2">
          <Share2 className="w-5 h-5" />
          Redes Coordenadas
        </h2>
        <span className="text-xs text-gray-500 font-mono">MAPA DE INFLUÊNCIA</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="border-tactical-accent/30 hover:bg-transparent">
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Identificação da Rede</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Perfis Suspeitos</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Data Detecção</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Risco</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                MAPEANDO CONEXÕES OCULTAS...
              </TableCell>
            </TableRow>
          ) : networks.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 font-mono">
                NENHUMA REDE COORDENADA DETECTADA NO RADAR.
              </TableCell>
            </TableRow>
          ) : (
            networks.map((n) => (
              <TableRow key={n.id} className="border-tactical-accent/10 hover:bg-tactical-accent/5 transition-colors">
                <TableCell className="font-bold text-gray-200 uppercase text-xs">
                  {n.nome_rede || `Cluster #${n.id.substring(0, 8)}`}
                </TableCell>
                <TableCell className="text-center font-mono text-tactical-accent">
                  {n.total_perfis}
                </TableCell>
                <TableCell className="text-center text-[10px] font-mono text-gray-500">
                  {new Date(n.data_deteccao || Date.now()).toLocaleDateString('pt-BR')}
                </TableCell>
                <TableCell className="text-right">
                  <Badge className="bg-orange-500 text-black border-none text-[9px] rounded-none uppercase font-bold">
                    {n.severidade || 'MODERADO'}
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
