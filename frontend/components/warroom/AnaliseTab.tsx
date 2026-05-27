'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Search, ShieldCheck } from 'lucide-react';
import { supabase } from '@/lib/supabase';

interface Comment {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  confianca_ia: number;
  is_hate: boolean;
  data_coleta: string;
  username_alvo: string;
}

export default function AnaliseTab() {
  const [limit, setLimit] = useState(50);
  const [isExpanding, setIsExpanding] = useState(false);

  const { data: comments = [], isLoading } = useQuery<Comment[]>({
    queryKey: ['analise-comments', limit],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('comentarios')
        .select('id, texto_bruto, categoria_ia, confianca_ia, is_hate, data_coleta, candidatos(username)')
        .not('categoria_ia', 'is', null)
        .order('data_coleta', { ascending: false })
        .limit(limit);

      if (error) throw error;
      
      return (data || []).map((c: any) => ({
        ...c,
        username_alvo: c.candidatos?.username || 'N/A'
      }));
    },
    refetchInterval: 15000,
  });

  const getRiskColor = (isHate: boolean, confidence: number) => {
    if (!isHate) return 'text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-900/10';
    if (confidence > 0.8) return 'text-red-600 dark:text-red-400 border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/10';
    if (confidence > 0.5) return 'text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-900 bg-orange-50 dark:bg-orange-900/10';
    return 'text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900 bg-yellow-50 dark:bg-yellow-900/10';
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <Search className="w-5 h-5 text-brand-primary" />
            Central de Análise
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Análise Semântica MCA v2.2</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-full">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-primary" />
          <span className="text-[10px] font-bold text-brand-primary uppercase">Audit Ativo</span>
        </div>
      </div>
      
      <Table>
        <TableHeader className="bg-bg-main/30">
          <TableRow className="border-border-main hover:bg-transparent">
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Alvo Monitorado</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Conteúdo em Análise</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Classificação</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-right px-6">Confiança</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
                PROCESSANDO PACOTES DE LINGUAGEM...
              </TableCell>
            </TableRow>
          ) : comments.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted font-mono text-xs">
                ESPECTRO LIMPO. NENHUMA DETECÇÃO NO PERÍODO.
              </TableCell>
            </TableRow>
          ) : (
            comments.map((c) => (
              <TableRow key={c.id} className="border-border-main hover:bg-bg-main/50 transition-colors">
                <TableCell className="px-6 py-4">
                  <div className="font-bold text-text-main text-sm">@{c.username_alvo}</div>
                  <div className="text-[10px] text-text-muted font-mono mt-0.5">
                    {new Date(c.data_coleta).toLocaleTimeString('pt-BR')}
                  </div>
                </TableCell>
                <TableCell className="max-w-md px-6 py-4">
                  <p className="text-sm text-text-main/80 italic leading-relaxed line-clamp-2" title={c.texto_bruto}>
                    "{c.texto_bruto}"
                  </p>
                </TableCell>
                <TableCell className="text-center py-4">
                  <Badge className={`px-2.5 py-0.5 text-[9px] font-black uppercase rounded-md border shadow-none ${getRiskColor(c.is_hate, c.confianca_ia)}`}>
                    {c.categoria_ia}
                  </Badge>
                </TableCell>
                <TableCell className="text-right px-6 py-4">
                  <div className="text-xs font-black text-text-main">
                    {(c.confianca_ia * 100).toFixed(1)}%
                  </div>
                  <div className="w-16 h-1 bg-bg-main rounded-full mt-1.5 ml-auto overflow-hidden">
                    <div 
                      className="h-full bg-brand-primary transition-all duration-1000" 
                      style={{ width: `${c.confianca_ia * 100}%` }}
                    />
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      <div className="p-4 bg-bg-main/30 border-t border-border-main text-center">
        <button 
          onClick={() => {
            setIsExpanding(true);
            setLimit(prev => prev + 50);
            setTimeout(() => setIsExpanding(false), 500);
          }}
          disabled={comments.length < limit || isExpanding}
          className="text-[10px] font-bold text-brand-primary uppercase tracking-widest hover:underline disabled:opacity-50 disabled:no-underline disabled:cursor-not-allowed"
        >
          {isExpanding 
            ? 'Carregando registros...' 
            : comments.length < limit 
              ? 'Todo o Histórico Carregado ✓' 
              : 'Carregar Histórico Completo →'
          }
        </button>
      </div>
    </div>
  );
}
