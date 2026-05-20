'use client';
import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/src/lib/supabase';

interface Comment {
  id: string;
  texto_bruto: string;
  pasa_classificacao: string;
  risco_score: string;
  created_at: string;
  username_alvo: string;
}

export default function ForensicTab() {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchComments() {
      try {
        const { data, error } = await supabase
          .from('comentarios')
          .select('id, texto_bruto, pasa_classificacao, risco_score, created_at, candidatos(username)')
          .not('pasa_classificacao', 'is', null)
          .order('created_at', { ascending: false })
          .limit(50);

        if (error) throw error;
        
        // Flattening the join for simplicity
        const formattedData = (data || []).map((c: any) => ({
          ...c,
          username_alvo: c.candidatos?.username || 'N/A'
        }));

        setComments(formattedData);
      } catch (error) {
        console.error("Erro ao buscar comentários:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchComments();
  }, []);

  const getRiskVariant = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'CRITICO': return 'destructive';
      case 'ELEVADO': return 'outline';
      case 'MODERADO': return 'secondary';
      default: return 'default';
    }
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
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Risco</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
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
                  <Badge className="bg-transparent border border-tactical-accent/30 text-[10px] text-tactical-accent">
                    {c.pasa_classificacao}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Badge variant={getRiskVariant(c.risco_score) as any} className="text-[10px] font-bold">
                    {c.risco_score || 'N/A'}
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
