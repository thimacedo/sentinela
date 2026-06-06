'use client';
/* eslint-disable @typescript-eslint/no-explicit-any, react/no-unescaped-entities */
import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Search, ShieldCheck, Calendar, Info, X } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import { supabase } from '@/lib/supabase';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSearchParams, useRouter } from 'next/navigation';

interface Comment {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  confianca_ia: number;
  is_hate: boolean;
  data_coleta: string;
  username_alvo: string;
  analise_pericial?: string;
  ccf_sync?: number; // Sincronização de bot/coordenação
}

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

  const getRiskColor = (category: string, isHate: boolean, confidence: number) => {
    if (category === 'ERRO') return 'text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-900 bg-purple-50 dark:bg-purple-900/10';
    if (!isHate) return 'text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-900/10';
    if (confidence > 0.8) return 'text-red-600 dark:text-red-400 border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/10';
    if (confidence > 0.5) return 'text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-900 bg-orange-50 dark:bg-orange-900/10';
    return 'text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900 bg-yellow-50 dark:bg-yellow-900/10';
  };

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
                {/* Post Card Estilo Rede Social */}
                <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm hover:border-brand-primary/20 transition-all duration-200">
                  {/* Cabeçalho do Post */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center font-black text-brand-primary text-sm">
                        {c.username_alvo.substring(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-black text-text-main text-sm">@{c.username_alvo}</span>
                          <span className="text-[10px] text-text-muted font-medium">• alvo monitorado</span>
                        </div>
                        <div className="flex items-center gap-1 text-[10px] text-text-muted font-mono mt-0.5">
                          <Calendar className="w-3 h-3" />
                          {new Date(c.data_coleta).toLocaleString('pt-BR')}
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                      <Badge className={`px-2.5 py-0.5 text-[9px] font-black uppercase rounded-sm border ${getRiskColor(c.categoria_ia, c.is_hate, c.confianca_ia)}`}>
                        {c.categoria_ia}
                      </Badge>
                      {c.ccf_sync && c.ccf_sync > 0.4 && (
                        <span className="text-[8px] font-black text-brand-primary bg-brand-primary/5 px-1.5 py-0.5 rounded border border-brand-primary/10 animate-pulse">
                          Coordenação: {(c.ccf_sync * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Conteúdo Central do Comentário */}
                  <div className="mt-4 p-5 bg-bg-main/50 border border-border-main rounded-xl overflow-x-auto">
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {c.texto_bruto}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Detalhes Técnicos (Se houver perícia) */}
                  {c.analise_pericial && (
                    <div className="mt-3 flex items-start gap-2 p-3 bg-brand-primary/5 rounded-lg border border-brand-primary/10">
                      <Info className="w-3.5 h-3.5 text-brand-primary shrink-0 mt-0.5" />
                      <div className="text-[10px] text-text-muted italic leading-relaxed">
                        <span className="font-bold text-brand-primary not-italic uppercase tracking-tighter mr-1">Parecer Técnico:</span>
                        {c.analise_pericial}
                      </div>
                    </div>
                  )}

                  {/* Rodapé do Card */}
                  <div className="mt-4 flex items-center justify-between gap-4 border-t border-border-main/50 pt-4">
                    <div className="flex items-center gap-2 w-full max-w-xs">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Confiança:</span>
                      <div className="text-xs font-black text-text-main w-12 text-right">
                        {(c.confianca_ia * 100).toFixed(1)}%
                      </div>
                      <div className="flex-1 h-1.5 bg-bg-main rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-1000 ${c.is_hate ? 'bg-brand-primary' : 'bg-emerald-500'}`} 
                          style={{ width: `${c.confianca_ia * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-[9px] font-mono text-text-muted opacity-50 uppercase">
                      ID: {c.id.substring(0, 8)}
                    </div>
                  </div>
                </div>

                {/* AdSense intercalado a cada 5 cards */}
                {(index + 1) % 5 === 0 && (
                  <div className="my-6 border border-border-main bg-bg-card rounded-2xl p-4 flex flex-col items-center shadow-sm">
                    <span className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-3">Publicidade Relacionada</span>
                    <AdSenseSlot adSlot="2020882637" format="horizontal" />
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
