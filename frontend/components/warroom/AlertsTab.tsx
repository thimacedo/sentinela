'use client';
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';

interface Alert {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  data_coleta: string;
  candidatos: { username: string };
  confianca_ia: number;
}

export default function AlertsTab() {
  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ['active-alerts-list'],
    queryFn: async () => {
      try {
        return await fetchApi('/api/v1/alerts/active');
      } catch (error) {
        console.warn("Erro ao buscar alertas da API, tentando fallback Supabase:", error);
      }

      // Fallback Supabase
      try {
        const { data: comments, error } = await supabase
          .from('comentarios')
          .select('id, texto_bruto, categoria_ia, data_coleta, candidato_id, confianca_ia')
          .eq('is_hate', true)
          .order('data_coleta', { ascending: false })
          .limit(20);

        if (error || !comments) {
          console.error("Erro no fallback Supabase de alertas:", error);
          return [];
        }

        return comments.map((c: any) => ({
          id: c.id,
          texto_bruto: c.texto_bruto,
          categoria_ia: c.categoria_ia || 'OUTROS',
          data_coleta: c.data_coleta,
          candidatos: { username: c.candidato_id || 'desconhecido' },
          confianca_ia: c.confianca_ia
        }));
      } catch (err) {
        console.error("Erro crítico no fallback de alertas do Supabase:", err);
        return [];
      }
    },
    refetchInterval: 10000,
  });

  return (
    <Card className="p-4 bg-black/50 border-tactical-accent">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-tactical-accent uppercase tracking-wider flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 animate-pulse" />
          Alertas Ativos
        </h2>
        <span className="text-xs text-red-500 font-mono animate-pulse">MONITORAMENTO EM TEMPO REAL</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="border-tactical-accent/30 hover:bg-transparent">
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Alvo</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Conteúdo Hostil</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-center">Data/Hora</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs text-right">Ação</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                ESCUTANDO FREQUÊNCIAS DE ÓDIO...
              </TableCell>
            </TableRow>
          ) : alerts.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500 font-mono">
                ESPECTRO LIMPO. NENHUM ALERTA ATIVO.
              </TableCell>
            </TableRow>
          ) : (
            alerts.map((a) => (
              <TableRow key={a.id} className="border-red-900/30 bg-red-950/5 hover:bg-red-900/10 transition-colors">
                <TableCell className="font-bold text-red-400 text-xs">
                  @{a.candidatos?.username}
                </TableCell>
                <TableCell className="max-w-md truncate text-xs text-gray-300">
                  <div className="flex flex-col gap-1">
                    <span className="italic">"{a.texto_bruto}"</span>
                    <Badge variant="destructive" className="w-fit text-[8px] h-4 rounded-none uppercase">
                      {a.categoria_ia}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell className="text-center text-[10px] font-mono text-gray-500">
                  {new Date(a.data_coleta).toLocaleString('pt-BR')}
                </TableCell>
                <TableCell className="text-right">
                  <button className="text-[9px] font-bold text-red-500 hover:text-red-400 uppercase border border-red-500/30 px-2 py-1 transition-all">
                    Neutralizar
                  </button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}
