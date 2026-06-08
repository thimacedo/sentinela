'use client';
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { FileText, Download, ShieldCheck, Lock, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import { useWallet } from '@/hooks/useWallet';

interface Dossier {
  id: string;
  candidato_id: string;
  data_geracao: string;
  arquivo_path: string;
  status: string;
}

export default function DossiersTab() {
  const router = useRouter();
  const { balance, refreshBalance } = useWallet();
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [unlocked, setUnlocked] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const saved = localStorage.getItem('sentinela_unlocked_dossiers');
    if (saved) {
      setTimeout(() => {
        setUnlocked(JSON.parse(saved));
      }, 0);
    }
  }, []);

  const { data: dossiers = [], isLoading } = useQuery<Dossier[]>({
    queryKey: ['dossiers-list'],
    queryFn: async () => {
      return await fetchApi('/api/v1/dossiers');
    },
    refetchInterval: 30000,
  });

  const handleUnlock = async (dossier: Dossier) => {
    setTimeout(async () => {
      if (unlocked[dossier.id]) {
        window.open(dossier.arquivo_path, '_blank');
        return;
      }

      if (balance < 350) {
        alert("Aporte Insuficiente. Recarregue seus Créditos de Inteligência (CI) para desbloquear este documento.");
        router.push('/planos');
        return;
      }

      const confirmUnlock = window.confirm("Desbloquear este Dossiê Analítico exigirá um aporte de 350 CI da sua carteira tática. Confirmar operação?");
      if (!confirmUnlock) return;

      try {
        setProcessingId(dossier.id);
        const userId = localStorage.getItem('sentinela_user_id');
        
        if (!userId) {
          alert("Sessão inválida. Por favor, faça login novamente.");
          return;
        }

        // PASA v94.1 - Centralização via API para Auditoria de Fraude
        const response = await fetchApi('/api/v1/ci/consume', {
          method: 'POST',
          body: JSON.stringify({
            user_id: userId,
            amount: 350,
            type: 'CONSUMPTION',
            description: `Desbloqueio de Dossiê: @${dossier.candidato_id}`
          })
        });

        if (response.status === 'success') {
          const newUnlocked = { ...unlocked, [dossier.id]: true };
          setUnlocked(newUnlocked);
          localStorage.setItem('sentinela_unlocked_dossiers', JSON.stringify(newUnlocked));
          refreshBalance();
          window.open(dossier.arquivo_path, '_blank');
        } else {
          alert("Falha na transação. Verifique se possui saldo suficiente e tente novamente.");
        }
      } catch (err: any) {
        console.error(err);
        if (err.message?.includes('402')) {
          alert("Aporte Insuficiente detectado. Saldo bloqueado.");
        } else {
          alert("Erro de comunicação com o servidor financeiro.");
        }
      } finally {
        setProcessingId(null);
      }
    }, 0);
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-primary" />
            Relatórios e Dossiês
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Exportação de Relatórios Analíticos</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase">Validade Técnica</span>
        </div>
      </div>

      <Table>
        <TableHeader className="bg-bg-main/30">
          <TableRow className="border-border-main hover:bg-transparent">
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Alvo do Dossiê</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Emissão</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Status</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-right px-6">Documento</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
                CONSOLIDANDO RELATÓRIOS DO SISTEMA...
              </TableCell>
            </TableRow>
          ) : dossiers.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted font-mono text-xs">
                NENHUM RELATÓRIO DISPONÍVEL NO MOMENTO.
              </TableCell>
            </TableRow>
          ) : (
            dossiers.map((d) => (
              <TableRow key={d.id} className="border-border-main hover:bg-bg-main/50 transition-colors">
                <TableCell className="px-6 py-4">
                  <div className="font-black text-text-main text-sm">@{d.candidato_id}</div>
                  <div className="text-[10px] text-text-muted font-mono mt-0.5 uppercase">Ref: {d.id.substring(0, 8)}</div>
                </TableCell>
                <TableCell className="px-6 py-4 text-xs text-text-muted">
                  {new Date(d.data_geracao).toLocaleString('pt-BR')}
                </TableCell>
                <TableCell className="text-center">
                  <Badge className="bg-brand-primary/10 text-brand-primary border border-brand-primary/20 text-[9px] font-black uppercase rounded-md shadow-none">
                    {d.status || 'CONCLUÍDO'}
                  </Badge>
                </TableCell>
                <TableCell className="text-right px-6 py-4">
                  <button 
                    onClick={() => handleUnlock(d)}
                    disabled={processingId === d.id}
                    className={`inline-flex items-center gap-2 px-3 py-1.5 border text-[10px] font-black uppercase rounded-lg transition-all shadow-sm ${
                      unlocked[d.id] 
                        ? 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-500' 
                        : 'bg-brand-primary/10 hover:bg-brand-primary hover:text-white border-brand-primary/30 text-brand-primary'
                    }`}
                  >
                    {processingId === d.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : unlocked[d.id] ? (
                      <Download className="w-3.5 h-3.5" />
                    ) : (
                      <Lock className="w-3.5 h-3.5" />
                    )}
                    {processingId === d.id ? 'Descriptografando...' : unlocked[d.id] ? 'Baixar PDF' : 'Desbloquear (350 CI)'}
                  </button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      <div className="p-4 bg-bg-main/30 border-t border-border-main text-center text-[10px] text-text-muted uppercase font-medium">
        Todos os relatórios são gerados com timestamp e integridade de dados.
      </div>
    </div>
  );
}
