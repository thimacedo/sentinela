'use client';
import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { ShieldAlert, Zap, Calendar, ShieldCheck, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import { useWallet } from '@/hooks/useWallet';
import { useInfiniteFeed, Comment } from '@/hooks/useInfiniteFeed';

import InvestigationModal from './alerts/InvestigationModal';
import AlertItem from './alerts/AlertItem';
import UnlockOverlay from './alerts/UnlockOverlay';

export default function AlertsTab() {
  const router = useRouter();
  const { balance, refreshBalance } = useWallet();
  const [unlocked, setUnlocked] = useState(false);

  const [investigatingAlert, setInvestigatingAlert] = useState<Comment | null>(null);

  const { items, loading, hasMore, loadMoreRef } = useInfiniteFeed();

  useEffect(() => {
    const unlockData = localStorage.getItem('sentinela_alerts_unlocked');
    if (unlockData) {
      const parsed = JSON.parse(unlockData);
      if (new Date().getTime() - parsed.timestamp < 24 * 60 * 60 * 1000) {
        setUnlocked(true);
      }
    }
  }, []);

  const handleUnlockSuccess = () => {
    setUnlocked(true);
    localStorage.setItem('sentinela_alerts_unlocked', JSON.stringify({ timestamp: new Date().getTime() }));
    refreshBalance();
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden relative">
      {/* Header */}
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-500 animate-pulse" />
            Alertas de Segurança
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Intelligence Feed (Round-Robin Buckets v92.8)</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 border rounded-full transition-colors ${unlocked ? 'bg-red-500/10 border-red-500/20' : 'bg-bg-card border-border-main'}`}>
          <Zap className={`w-3.5 h-3.5 ${unlocked ? 'text-red-500 fill-red-500' : 'text-text-muted'}`} />
          <span className={`text-[10px] font-bold uppercase ${unlocked ? 'text-red-600 dark:text-red-400' : 'text-text-muted'}`}>
            {unlocked ? 'Live Monitor' : 'Defasado (12h)'}
          </span>
        </div>
      </div>

      <div className="relative">
        <div className={!unlocked ? 'blur-sm opacity-50 transition-all duration-700' : ''}>
          <div className="p-6 space-y-6 bg-bg-main/10 min-h-[500px]">
            {items.length === 0 && !loading ? (
              <div className="text-center py-20 text-text-muted font-mono text-xs">
                ESPECTRO LIMPO. NENHUM INCIDENTE ATIVO.
              </div>
            ) : (
              <div className="flex flex-col gap-6 max-w-2xl mx-auto">
                {items.map((item) => {
                  if (item.type === 'comment') {
                    return (
                      <AlertItem 
                        key={item.data.id} 
                        alert={item.data} 
                        unlocked={unlocked} 
                        onInvestigate={setInvestigatingAlert} 
                      />
                    );
                  } else if (item.type === 'chart') {
                    return (
                      <div key={item.id} className="my-2 border border-border-main bg-bg-card rounded-2xl p-6 shadow-sm">
                         <span className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-4 block">Visualização de Tendência Recente</span>
                         <div className="h-40 bg-bg-main/30 rounded-xl animate-pulse flex items-center justify-center text-[10px] font-mono text-slate-600">
                           [COMPONENT: RECHART_MINI_VOYANT]
                         </div>
                      </div>
                    );
                  } else if (item.type === 'ad') {
                    return (
                      <div key={item.id} className="my-2 border border-border-main bg-bg-card rounded-2xl p-4 flex flex-col items-center shadow-sm">
                        <span className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-3">Publicidade Cívica Relacionada</span>
                        <AdSenseSlot adSlot="2020882637" format="horizontal" />
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            )}

            {/* Div Sentinela para o Scroll Infinito */}
            <div ref={loadMoreRef} className="py-8 flex justify-center items-center">
              {loading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-red-500" />
                  <span className="text-[10px] font-black text-red-600 dark:text-red-400 uppercase tracking-widest">
                    Sincronizando incidentes...
                  </span>
                </div>
              ) : hasMore ? (
                <div className="h-1" />
              ) : (
                <span className="text-[10px] font-bold text-text-muted uppercase tracking-tighter">Fim da Transmissão</span>
              )}
            </div>
          </div>
        </div>

        {/* Lock Overlay */}
        {!unlocked && (
          <UnlockOverlay balance={balance} onSuccess={handleUnlockSuccess} />
        )}
      </div>

      {/* Modal de Investigação */}
      {investigatingAlert && (
        <InvestigationModal 
          investigatingAlert={investigatingAlert} 
          onClose={() => setInvestigatingAlert(null)} 
        />
      )}
    </div>
  );
}
