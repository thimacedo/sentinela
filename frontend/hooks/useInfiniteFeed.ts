"use client";
import { useState, useEffect, useRef, useCallback } from 'react';

export interface Comment {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  data_coleta: string;
  candidatos?: { username: string; foto_url?: string } | null;
}

type FeedItem = 
  | { type: 'comment'; data: Comment; id: string }
  | { type: 'chart'; id: string }
  | { type: 'ad'; id: string };

const FETCH_LIMIT = 30; // Buscamos mais do que mostramos para encher os baldes
const RENDER_BATCH = 5;  // Renderizamos de 5 em 5 para ir preenchendo a tela suavemente
const CHART_INTERVAL = 12; 
const AD_INTERVAL = 25;    

/**
 * Hook de Feed Infinito com Inteligência de Distribuição (PASA v92.8).
 * Implementa Round-Robin de Buckets para evitar repetição consecutiva do mesmo alvo.
 */
export function useInfiniteFeed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  
  // Baldes de comentários por candidato
  const bucketsRef = useRef<Record<string, Comment[]>>({});
  const candidateKeysRef = useRef<string[]>([]);
  const offsetRef = useRef(0);
  const renderedCommentsCountRef = useRef(0);
  
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Função que distribui os comentários da API nos baldes de cada candidato
  const distributeToBuckets = useCallback((comments: Comment[]) => {
    comments.forEach(comment => {
      // Chave do balde é o username do alvo
      const key = comment.candidatos?.username || 'alvo_desconhecido';
      
      if (!bucketsRef.current[key]) {
        bucketsRef.current[key] = [];
      }
      // Evita duplicados no balde (idempotência visual)
      if (!bucketsRef.current[key].some(c => c.id === comment.id)) {
        bucketsRef.current[key].push(comment);
      }
    });

    // Atualiza a lista de chaves disponíveis (apenas as que têm comentários)
    candidateKeysRef.current = Object.keys(bucketsRef.current).filter(k => bucketsRef.current[k].length > 0);
  }, []);

  // Função que retira 1 comentário de cada alvo alternadamente (Round-Robin)
  const popFromBuckets = useCallback((count: number): Comment[] => {
    const result: Comment[] = [];
    let currentKeys = [...candidateKeysRef.current];
    
    // Se não tiver mais nada nos baldes, retorna vazio
    if (currentKeys.length === 0) return result;

    while (result.length < count && currentKeys.length > 0) {
      // CASO ESPECIAL: Se só tem 1 alvo no balde, permite repetição (senão a tela trava)
      if (currentKeys.length === 1) {
        const onlyKey = currentKeys[0];
        const comment = bucketsRef.current[onlyKey].shift();
        if (comment) result.push(comment);
        
        // Se esvaziou o único balde, limpa a chave
        if (bucketsRef.current[onlyKey].length === 0) {
          delete bucketsRef.current[onlyKey];
          currentKeys = [];
        }
      } 
      // CASO NORMAL: Round-Robin rigoroso (Pega 1 do primeiro, passa ele pro fim da fila)
      else {
        const nextKey = currentKeys.shift()!;
        const comment = bucketsRef.current[nextKey].shift();
        
        if (comment) {
          result.push(comment);
        }
        
        // Se ainda sobrou comentário nesse balde, ele vai para o final da fila de espera
        if (bucketsRef.current[nextKey].length > 0) {
          currentKeys.push(nextKey);
        } else {
          // Se esvaziou, deleta o balde
          delete bucketsRef.current[nextKey];
        }
      }
    }

    // Atualiza as chaves globais para o próximo ciclo
    candidateKeysRef.current = Object.keys(bucketsRef.current).filter(k => bucketsRef.current[k].length > 0);

    return result;
  }, []);

  const loadMoreItems = useCallback(() => {
    if (loading) return;

    // Se tem coisa no balde, renderiza daqui mesmo (sem chamar a API)
    if (candidateKeysRef.current.length > 0) {
      const newComments = popFromBuckets(RENDER_BATCH);
      if (newComments.length > 0) {
        const newItems: FeedItem[] = newComments.map(c => ({ type: 'comment', data: c, id: c.id }));
        
        const prevCount = renderedCommentsCountRef.current;
        const nextCount = prevCount + newItems.length;

        // Injeta Gráfico no intervalo correto
        if (nextCount >= CHART_INTERVAL && prevCount < CHART_INTERVAL) {
           newItems.splice(Math.floor(newItems.length / 2), 0, { type: 'chart', id: `chart-${nextCount}` });
        }

        // Injeta AdSense no intervalo correto
        if (nextCount >= AD_INTERVAL && prevCount < AD_INTERVAL) {
           newItems.push({ type: 'ad', id: `ad-${nextCount}` });
        }

        renderedCommentsCountRef.current = nextCount;
        setItems(prev => [...prev, ...newItems]);
      }
      return;
    }

    // Se os baldes estão vazios, busca da API
    if (!hasMore) return;
    setLoading(true);

    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '';
    fetch(`${apiBase}/api/v1/alerts/active?limit=${FETCH_LIMIT}&offset=${offsetRef.current}`)
      .then(res => res.json())
      .then((data: Comment[]) => {
        if (data.length === 0) {
          setHasMore(false);
        } else {
          offsetRef.current += FETCH_LIMIT;
          distributeToBuckets(data);
          
          // Recursivamente chama para já renderizar o que acabou de entrar no balde
          loadMoreItems();
        }
      })
      .catch(err => {
        console.error("[Feed] Fetch error:", err);
        setHasMore(false); // Evita loop infinito em erro
      })
      .finally(() => setLoading(false));

  }, [loading, hasMore, distributeToBuckets, popFromBuckets]);

  // Configuração do Intersection Observer (Rolagem Infinita)
  useEffect(() => {
    if (observerRef.current) observerRef.current.disconnect();

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMoreItems();
      },
      { rootMargin: "400px" } // Dispara bem antes do fim para parecer infinito de verdade
    );

    if (loadMoreRef.current) observerRef.current.observe(loadMoreRef.current);

    return () => observerRef.current?.disconnect();
  }, [loadMoreItems]);

  // Primeiro carregamento
  useEffect(() => { loadMoreItems(); }, []);

  return { items, loading, hasMore, loadMoreRef };
}
