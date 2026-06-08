'use client';
/* eslint-disable @typescript-eslint/no-explicit-any, react/no-unescaped-entities */
import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Search, ShieldCheck, Calendar, Info, X } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import { supabase } from '@/lib/supabase';
import { useSearchParams, useRouter } from 'next/navigation';
import CommentCard, { Comment } from './analise/CommentCard';

export default function AnaliseTab() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const targetParam = searchParams.get('target');

  // Shadowban Léxico (Limpeza Analítica)
  const [shadowbanActive, setShadowbanActive] = useState(true);

  // Paginação e scroll infinito
  const [visibleCount, setVisibleCount] = useState(10);
  const [apiLimit, setApiLimit] = useState(50);
  const observerRef = useRef<HTMLDivElement>(null);

  const { data: comments = [], isLoading } = useQuery<Comment[]>({
    queryKey: ['analise-comments', apiLimit, targetParam],
    queryFn: async () => {
      let query = supabase
        .from('comentarios')
        .select('id, texto_bruto, categoria_ia, confianca_ia, is_hate, data_coleta, analise_pericial, ccf_sync, candidatos!inner(username)')
        .not('categoria_ia', 'is', null);

      if (targetParam) {
        query = query.eq('candidatos.username', targetParam);
      }

      const { data, error } = await query
        .order('data_coleta', { ascending: false })
        .limit(apiLimit);

      if (error) throw error;
      
      return (data || []).map((c: any) => ({
        ...c,
        username_alvo: c.candidatos?.username || 'N/A'
      }));
    },
    refetchInterval: 15000,
  });

  // Filtro de Shadowban Léxico: Oculta ataques coordenados (Sync > 80%) se o filtro estiver ativo
  const displayedComments = shadowbanActive 
    ? comments.filter(c => (c.ccf_sync || 0) < 0.8 || c.categoria_ia === 'ATAQUE_INSTITUCIONAL') // Mantém institucionais mesmo se sync for alto
    : comments;

  // Observer para Wall Infinito
  useEffect(() => {
    if (!observerRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => {
            const nextVal = prev + 10;
            if (nextVal >= apiLimit - 5) {
              setApiLimit((prevLimit) => prevLimit + 50);
            }
            return nextVal;
          });
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(observerRef.current);
    return () => observer.disconnect();
  }, [apiLimit, comments.length]);



  const clearTargetFilter = () => {
    router.push('/analise');
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <Search className="w-5 h-5 text-brand-primary" />
            Central de Análise
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Análise Semântica MCA v2.2</p>
          
          {targetParam && (
            <div className="mt-2 flex items-center gap-2">
              <Badge className="bg-brand-primary/10 text-brand-primary border-brand-primary/20 flex items-center gap-1.5 px-2 py-0.5">
                Filtrando: @{targetParam}
                <button onClick={clearTargetFilter} className="hover:text-brand-primary/70 transition-colors">
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-border-main">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-tighter">Shadowban Léxico</span>
            <button 
              onClick={() => setShadowbanActive(!shadowbanActive)}
              className={`w-8 h-4 rounded-full relative transition-all ${shadowbanActive ? 'bg-brand-primary' : 'bg-slate-300 dark:bg-slate-700'}`}
            >
              <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${shadowbanActive ? 'left-4.5' : 'left-0.5'}`} />
            </button>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5 text-brand-primary" />
            <span className="text-[10px] font-bold text-brand-primary uppercase">Audit Ativo</span>
          </div>
        </div>
      </div>

      {/* Feed de Análise (Rede Social) */}
      <div className="p-6 space-y-6 bg-bg-main/10">
        {isLoading && comments.length === 0 ? (
          <div className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
            PROCESSANDO PACOTES DE LINGUAGEM...
          </div>
        ) : displayedComments.length === 0 ? (
          <div className="text-center py-20 text-text-muted font-mono text-xs">
            {targetParam 
              ? `NENHUMA DETECÇÃO LOCALIZADA PARA @${targetParam.toUpperCase()}.`
              : 'ESPECTRO LIMPO. NENHUMA DETECÇÃO NO PERÍODO.'}
            {shadowbanActive && comments.length > 0 && (
              <p className="mt-2 text-brand-primary animate-pulse">Itens ocultados pelo Shadowban Léxico.</p>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-6 max-w-2xl mx-auto">
            {displayedComments.slice(0, visibleCount).map((c, index) => (
              <div key={c.id} className="w-full">
                <CommentCard c={c} />

                {/* AdSense intercalado a cada 5 cards */}
                {(index + 1) % 5 === 0 && (
                  <div className="my-6 border border-border-main bg-bg-card rounded-2xl p-4 flex flex-col items-center shadow-sm">
                    <span className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-3">Publicidade Relacionada</span>
                    <AdSenseSlot adSlot="2020882637" slotId={`feed-ad-${index}`} format="horizontal" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Div para o Scroll Infinito */}
        {comments.length > visibleCount && (
          <div ref={observerRef} className="py-8 flex justify-center items-center">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce" />
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce delay-100" />
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce delay-200" />
              <span className="text-[10px] font-black text-brand-primary uppercase tracking-widest ml-2">
                Carregando mais análises...
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
