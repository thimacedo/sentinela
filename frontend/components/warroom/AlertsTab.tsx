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

export default function AlertsTab() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { balance, refreshBalance } = useWallet();
  const [unlocked, setUnlocked] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [investigatingAlert, setInvestigatingAlert] = useState<Comment | null>(null);
  const [analiseTexto, setAnaliseTexto] = useState('');
  const [isSaving, setIsSaving] = useState(false);

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

  const handleUnlock = async () => {
    if (balance < 850) {
      alert("Aporte Insuficiente. Adquira mais Créditos de Inteligência (CI) para operar o Feed de Alertas em Tempo Real.");
      router.push('/planos');
      return;
    }

    const confirmUnlock = window.confirm("Monitorar a rede em tempo real exige uma carga massiva de processamento. Deseja investir 850 CI para liberar o feed por 24 horas?");
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
        p_amount: -850,
        p_type: 'CONSUMPTION',
        p_session_id: null,
        p_metadata: { action: 'unlock_alerts' }
      });

      if (error) throw error;

      if (data === true) {
        setUnlocked(true);
        localStorage.setItem('sentinela_alerts_unlocked', JSON.stringify({ timestamp: new Date().getTime() }));
        refreshBalance();
      } else {
        alert("Falha na transação. Saldo insuficiente.");
      }
    } catch (err) {
      console.error(err);
      alert("Erro ao processar transação.");
    } finally {
      setIsProcessing(false);
    }
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
                    const a = item.data;
                    return (
                      <div key={a.id} className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm hover:border-red-500/20 transition-all duration-200">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center font-black text-red-600 text-sm">
                              {a.candidatos?.username?.substring(0, 2).toUpperCase() || '??'}
                            </div>
                            <div>
                              <div className="flex items-center gap-1.5">
                                <span className="font-black text-text-main text-sm">@{a.candidatos?.username || 'desconhecido'}</span>
                                <span className="text-[10px] text-text-muted font-medium">• alvo afetado</span>
                              </div>
                              <div className="flex items-center gap-1 text-[10px] text-text-muted font-mono mt-0.5">
                                <Calendar className="w-3 h-3" />
                                {new Date(a.data_coleta).toLocaleString('pt-BR')}
                              </div>
                            </div>
                          </div>
                          <Badge className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 text-[8px] font-black uppercase rounded-sm h-4">
                            {a.categoria_ia}
                          </Badge>
                        </div>

                        <div className="mt-4 p-4 bg-bg-main/50 border border-border-main rounded-xl">
                          <p className="text-sm text-text-main leading-relaxed italic">
                            "{unlocked ? a.texto_bruto : "Conteúdo defasado (Acesso Premium Necessário)"}"
                          </p>
                        </div>

                        <div className="mt-4 flex items-center justify-between gap-4 border-t border-border-main/50 pt-4">
                          <button 
                            onClick={() => {
                              setInvestigatingAlert(a);
                              setAnaliseTexto('');
                            }}
                            className="flex items-center gap-2 px-3 py-1.5 bg-bg-card hover:bg-bg-main border border-border-main text-[10px] font-black uppercase text-red-600 dark:text-red-400 rounded-lg transition-all shadow-sm"
                          >
                            <ShieldCheck className="w-3.5 h-3.5" />
                            Investigar
                          </button>
                        </div>
                      </div>
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
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-bg-card/30 backdrop-blur-[1px] mt-[80px]">
            <div className="bg-bg-main border border-red-500/20 rounded-2xl p-8 max-w-md text-center shadow-2xl flex flex-col items-center animate-in slide-in-from-bottom-4 duration-500">
              <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6">
                <ShieldAlert className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-xl font-black text-text-main mb-2">Dados Defasados</h3>
              <p className="text-sm text-text-muted mb-8 leading-relaxed">
                Você está visualizando incidentes com 12 horas de atraso. Para reagir a crises rapidamente, libere o monitoramento em tempo real.
              </p>
              <button 
                onClick={handleUnlock}
                disabled={isProcessing}
                className="w-full py-4 rounded-xl bg-red-600 text-white font-black uppercase tracking-widest text-[10px] hover:bg-red-700 transition-all shadow-lg shadow-red-500/20 flex items-center justify-center gap-2"
              >
                {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4 fill-white" />}
                Liberar Feed em Tempo Real (850 CI)
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal de Investigação */}
      {investigatingAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-bg-card border border-border-main rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
              <div>
                <h3 className="text-lg font-black text-text-main tracking-tight uppercase">Análise Analítica de Indício</h3>
              </div>
              <button onClick={() => setInvestigatingAlert(null)} className="text-text-muted hover:text-text-main text-xs font-bold uppercase tracking-wider transition-colors">Fechar</button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Alvo</span>
                <div className="font-black text-red-600 dark:text-red-400 text-sm mt-1">@{investigatingAlert.candidatos?.username}</div>
              </div>
              
              <div>
                <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Conteúdo Analisado</span>
                <div className="p-3 bg-bg-main/50 border border-border-main rounded-lg text-xs text-text-main/90 italic mt-1 italic">
                  "{investigatingAlert.texto_bruto}"
                </div>
              </div>

              <div>
                <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Indícios e Análise de Linguagem</label>
                <textarea 
                  rows={4}
                  value={analiseTexto}
                  onChange={(e) => setAnaliseTexto(e.target.value)}
                  placeholder="Descreva aqui os indícios linguísticos..."
                  className="w-full p-3 bg-bg-main/50 border border-border-main rounded-lg text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors leading-relaxed placeholder:text-text-muted"
                />
              </div>
            </div>

            <div className="p-4 bg-bg-main/30 border-t border-border-main flex justify-between gap-3">
              <button 
                onClick={async () => {
                  if (!investigatingAlert) return;
                  setIsSaving(true);
                  try {
                    await fetchApi('/api/v1/alerts/false-positive', { method: 'POST', body: JSON.stringify({ id: investigatingAlert.id }) });
                    queryClient.invalidateQueries({ queryKey: ['active-alerts-list'] });
                    setInvestigatingAlert(null);
                  } catch (err) { console.error(err); } finally { setIsSaving(false); }
                }}
                disabled={isSaving}
                className="px-3 py-2 border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 text-[10px] font-black uppercase text-red-600 dark:text-red-400 rounded-lg transition-all"
              >
                Descartar (Falso Positivo)
              </button>
              <div className="flex gap-2">
                <button onClick={() => setInvestigatingAlert(null)} className="px-3 py-2 border border-border-main bg-bg-card hover:bg-bg-main text-[10px] font-bold uppercase text-text-muted hover:text-text-main rounded-lg transition-all">Cancelar</button>
                <button 
                  onClick={async () => {
                    if (!investigatingAlert) return;
                    setIsSaving(true);
                    try {
                      await fetchApi('/api/v1/audit/validate', { method: 'POST', body: JSON.stringify({ comment_id: investigatingAlert.id, rotulo_correto: 'hate', analise_pericial: analiseTexto }) });
                      queryClient.invalidateQueries({ queryKey: ['active-alerts-list'] });
                      setInvestigatingAlert(null);
                    } catch (err) { console.error(err); } finally { setIsSaving(false); }
                  }}
                  disabled={isSaving}
                  className="px-4 py-2 bg-brand-primary hover:bg-brand-primary/90 text-[10px] font-black uppercase text-white rounded-lg transition-all shadow-md"
                >
                  {isSaving ? 'Salvando...' : 'Salvar Análise'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
