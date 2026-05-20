'use client';
import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { supabase } from '@/src/lib/supabase';
import { Badge } from '@/components/ui/badge';

interface Target {
  id: string;
  username: string;
  status_monitoramento: string;
  tier: string;
}

export default function TargetsTab() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTargets() {
      try {
        const { data, error } = await supabase
          .from('candidatos')
          .select('id, username, status_monitoramento, tier')
          .eq('status_monitoramento', 'Ativo')
          .order('username', { ascending: true });

        if (error) throw error;
        setTargets(data || []);
      } catch (error) {
        console.error("Erro ao buscar alvos:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchTargets();
  }, []);

  return (
    <Card className="p-4 bg-black/50 border-tactical-accent">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-tactical-accent uppercase tracking-wider">Alvos Ativos</h2>
        <span className="text-xs text-gray-500 font-mono">TOTAL: {targets.length}</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="border-tactical-accent/30 hover:bg-transparent">
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Username</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Status</TableHead>
            <TableHead className="text-tactical-accent/70 uppercase text-xs">Tier</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell colSpan={3} className="text-center py-8 text-gray-500 animate-pulse font-mono">
                Sincronizando com a rede...
              </TableCell>
            </TableRow>
          ) : targets.length === 0 ? (
            <TableRow>
              <TableCell colSpan={3} className="text-center py-8 text-gray-500 font-mono">
                Nenhum alvo ativo no radar.
              </TableCell>
            </TableRow>
          ) : (
            targets.map((t) => (
              <TableRow key={t.id} className="border-tactical-accent/10 hover:bg-tactical-accent/5 transition-colors">
                <TableCell className="font-bold text-gray-200">@{t.username}</TableCell>
                <TableCell>
                  <Badge className="bg-tactical-accent text-black hover:bg-tactical-accent/80 border-none rounded-none text-[10px] font-bold">
                    {t.status_monitoramento}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-xs text-tactical-accent/60">
                  {t.tier || 'N/A'}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}
