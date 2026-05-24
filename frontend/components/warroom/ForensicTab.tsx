'use client';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/src/lib/supabase';

interface Comment {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  confianca_ia: number;
  is_hate: boolean;
  data_coleta: string;
  username_alvo: string;
}

export default function ForensicTab() {
  const { data: comments = [], isLoading } = useQuery<Comment[]>({
    queryKey: ['forensic-comments'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('comentarios')
        .select('id, texto_bruto, categoria_ia, confianca_ia, is_hate, data_coleta, candidatos(username)')
        .not('categoria_ia', 'is', null)
        .order('data_coleta', { ascending: false })
        .limit(50);

      if (error) throw error;
      
      return (data || []).map((c: any) => ({
        ...c,
        username_alvo: c.candidatos?.username || 'N/A'
      }));
    },
    refetchInterval: 15000,
  });

  const getRiskColor = (isHate: boolean, confidence: number) => {
    if (!isHate) return 'text-emerald-400';
    if (confidence > 0.8) return 'text-red-500';
    if (confidence > 0.5) return 'text-orange-500';
    return 'text-yellow-500';
  };

  return (
    <Card className="p-4 bg-black/50 border-tactical-accent">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-tactical-accent uppercase tracking-wider">Detecções Recentes</h2>
        <span className="text-xs text-gray-500 font-mono">ÚLTIMAS 50 CAPTURAS</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="border-tactical-accent/30 hover:bg-transparent">
            <TableHead className="text-tactical-accent/70 uppercase text-xs w-[150px]">Alvo</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Conteúdo Analisado</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Classificação</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Confiança</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                Descriptografando pacotes de dados...
              </TableCell>
            </TableRow>
          ) : comments.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 font-mono">
                Nenhuma detecção confirmada no período.
              </TableCell>
            </TableRow>
          ) : (
            comments.map((c) => (
              <TableRow key={c.id} className="border-tactical-accent/10 hover:bg-tactical-accent/5 transition-colors">
                <TableCell className="font-bold text-tactical-accent/80 text-xs">
                  @{c.username_alvo}
                </TableCell>
                <TableCell className="max-w-md truncate text-xs text-gray-300 italic" title={c.texto_bruto}>
                  "{c.texto_bruto}"
                </TableCell>
                <TableCell className="text-center">
                  <Badge className={`bg-transparent border border-tactical-accent/30 text-[10px] ${getRiskColor(c.is_hate, c.confianca_ia)}`}>
                    {c.categoria_ia}
                  </Badge>
                </TableCell>
                <TableCell className="text-right font-mono text-[10px] text-gray-500">
                  {(c.confianca_ia * 100).toFixed(1)}%
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}

