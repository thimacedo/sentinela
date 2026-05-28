'use client';
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Share2, Globe, EyeOff, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import { useWallet } from '@/hooks/useWallet';

interface Network {
  id: string;
  nome_rede: string;
  total_perfis: number;
  data_deteccao: string;
  severidade: string;
}

export default function NetworkTab() {
  const router = useRouter();
  const { balance, refreshBalance } = useWallet();
  const [unlocked, setUnlocked] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Verifica se já foi desbloqueado (sessão local temporária ou 24h)
    const unlockData = localStorage.getItem('sentinela_radar_unlocked');
    if (unlockData) {
      const parsed = JSON.parse(unlockData);
      // Desbloqueio válido por 24 horas
      if (new Date().getTime() - parsed.timestamp < 24 * 60 * 60 * 1000) {
        setTimeout(() => {
          setUnlocked(true);
        }, 0);
      }
    }
  }, []);

  const { data: networks = [], isLoading } = useQuery<Network[]>({
    queryKey: ['networks-clusters'],
    queryFn: async () => {
      return await fetchApi('/api/v1/networks');
    },
    refetchInterval: 60000,
  });

  const handleUnlock = async () => {
    setTimeout(async () => {
      if (balance < 150) {
        alert("Aporte Insuficiente. Adquira mais Créditos de Inteligência (CI) para operar o Radar de Narrativas.");
        router.push('/planos');
        return;
      }

      const confirmUnlock = window.confirm("Revelar as redes de influência consumirá 150 CI da sua carteira (acesso por 24 horas). Confirmar operação?");
      if (!confirmUnlock) return;

      try {
        setIsProcessing(true);
        const userId = localStorage.getItem('sentinela_user_id');
        
        if (!userId) {
          alert("Sessão inválida. Faça login.");
          return;
        }

        const { data, error } = await supabase.rpc('process_stn_transaction', {
          p_user_id: userId,
          p_amount: -150,
          p_type: 'CONSUMPTION',
          p_session_id: null,
          p_metadata: { action: 'unlock_radar' }
        });

        if (error) throw error;

        if (data === true) {
          setUnlocked(true);
          localStorage.setItem('sentinela_radar_unlocked', JSON.stringify({ timestamp: new Date().getTime() }));
          refreshBalance();
        } else {
          alert("Falha na transação. Saldo insuficiente.");
        }
      } catch (err) {
        console.error(err);
        alert("Erro ao conectar com a malha neural de pagamentos.");
      } finally {
        setIsProcessing(false);
      }
    }, 0);
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden relative">
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

      <div className="relative">
        <div className={!unlocked ? 'blur-md pointer-events-none select-none opacity-40 transition-all duration-700' : ''}>
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
        </div>

        {/* Lock Overlay */}
        {!unlocked && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-bg-card/40 backdrop-blur-[2px]">
            <div className="bg-bg-main border border-border-main rounded-2xl p-8 max-w-md text-center shadow-2xl flex flex-col items-center animate-in zoom-in-95 duration-500">
              <div className="w-16 h-16 bg-brand-primary/10 rounded-full flex items-center justify-center mb-6">
                <EyeOff className="w-8 h-8 text-brand-primary" />
              </div>
              <h3 className="text-xl font-black text-text-main mb-2">Visão Tática Obscurecida</h3>
              <p className="text-sm text-text-muted mb-8 leading-relaxed">
                Este módulo exibe conexões ocultas e arquiteturas de desinformação em tempo real.
              </p>
              <button 
                onClick={handleUnlock}
                disabled={isProcessing}
                className="w-full py-4 rounded-xl bg-brand-primary text-white font-black uppercase tracking-widest text-[10px] hover:bg-brand-primary/90 transition-all shadow-lg shadow-brand-primary/20 flex items-center justify-center gap-2"
              >
                {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
                Investir 150 CI (Radar 24h)
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 bg-bg-main/30 border-t border-border-main text-center text-[10px] text-text-muted uppercase tracking-widest font-medium">
        Algoritmo de Detecção de Padrões Coordenados Ativo
      </div>
    </div>
  );
}
