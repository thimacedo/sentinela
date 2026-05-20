'use client';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { FileText, Download } from 'lucide-react';

interface Dossier {
  id: string;
  candidato_id: string;
  data_geracao: string;
  pdf_url: string;
  status: string;
}

export default function DossiersTab() {
  const { data: dossiers = [], isLoading } = useQuery<Dossier[]>({
    queryKey: ['dossiers-list'],
    queryFn: async () => {
      const response = await fetch('/api/v1/dossiers');
      if (!response.ok) throw new Error('Falha ao buscar dossiês');
      return await response.json();
    },
    refetchInterval: 30000,
  });

  return (
    <Card className="p-4 bg-black/50 border-tactical-accent">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-tactical-accent uppercase tracking-wider">Dossiês Forenses</h2>
        <span className="text-xs text-gray-500 font-mono">RELATÓRIOS CONSOLIDADOS</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="border-tactical-accent/30 hover:bg-transparent">
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Alvo</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Data de Geração</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Status</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Ação</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                RECUPERANDO ARQUIVOS CRIPTOGRAFADOS...
              </TableCell>
            </TableRow>
          ) : dossiers.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 font-mono">
                NENHUM DOSSIÊ GERADO ATÉ O MOMENTO.
              </TableCell>
            </TableRow>
          ) : (
            dossiers.map((d) => (
              <TableRow key={d.id} className="border-tactical-accent/10 hover:bg-tactical-accent/5 transition-colors">
                <TableCell className="font-bold text-gray-200 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-tactical-accent/50" />
                  @{d.candidato_id}
                </TableCell>
                <TableCell className="text-xs text-gray-400">
                  {new Date(d.data_geracao).toLocaleString('pt-BR')}
                </TableCell>
                <TableCell className="text-center">
                  <Badge className="bg-tactical-accent/20 text-tactical-accent border border-tactical-accent/50 text-[9px] rounded-none uppercase font-bold">
                    {d.status || 'CONCLUÍDO'}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <a 
                    href={d.pdf_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[10px] font-bold text-tactical-accent hover:underline uppercase"
                  >
                    <Download className="w-3 h-3" />
                    Baixar PDF
                  </a>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}
