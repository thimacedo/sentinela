'use client';
import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Share2, Globe, EyeOff, Loader2, Network as NetworkIcon, Users } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import { useWallet } from '@/hooks/useWallet';
import dynamic from 'next/dynamic';

// Dynamic import do Wrapper para garantir SSR seguro
const ForceGraphWrapper = dynamic(() => import('./ForceGraphWrapper'), {
  ssr: false,
  loading: () => <div className="w-full h-[500px] flex items-center justify-center text-text-muted animate-pulse font-mono text-[10px] uppercase bg-slate-900 rounded-xl">Iniciando Motor de Renderização...</div>
});

interface Network {
  id: string;
  nome_rede: string;
  tipo_coordenacao?: string;
  score_perigoso?: number;
  nodes?: string[];
  edges?: any[];
  estatisticas?: any;
  created_at: string;
}

export default function NetworkTab() {
  const router = useRouter();
  const { balance, refreshBalance } = useWallet();
  const [unlocked, setUnlocked] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedNetwork, setSelectedNetwork] = useState<Network | null>(null);

  useEffect(() => {
    // Modo Stress Test: Auto-unlock
    setTimeout(() => {
      setUnlocked(true);
    }, 500);
  }, []);

  const { data: networks = [], isLoading } = useQuery<Network[]>({
    queryKey: ['networks-clusters'],
    queryFn: async () => {
      return await fetchApi('/api/v1/networks');
    },
    refetchInterval: 60000,
  });

  // Transforma os dados do banco para o formato esperado pelo react-force-graph
  const graphData = useMemo(() => {
    if (!selectedNetwork || !selectedNetwork.nodes || !selectedNetwork.edges) {
      // Retorna grafo vazio de placeholder
      return { nodes: [], links: [] };
    }

    // Extrair contas multi-target (se houver flag ou heurística na estatística)
    const multiAttackers = selectedNetwork.estatisticas?.contas_coordenadas || 0;

    const nodes = selectedNetwork.nodes.map((nodeId: string) => {
      // Heurística de UI: Se o nó for um autor atacando, cor vermelha/laranja. Se for alvo, azul.
      // O banco armazena misturado, vamos assumir que nós com mais edges de "saída" são autores.
      const isAttacker = selectedNetwork.edges?.some((e: any) => e.from === nodeId);
      return {
        id: nodeId,
        name: nodeId,
        // Destaque visual
        val: isAttacker ? 2 : 5, 
        color: isAttacker ? (multiAttackers > 0 ? '#ef4444' : '#f59e0b') : '#3b82f6',
        isAttacker
      };
    });

    const links = selectedNetwork.edges.map((edge: any) => ({
      source: edge.from,
      target: edge.to,
      weight: edge.weight,
      // Quanto maior o peso (repetição do ataque), mais grossa e vermelha a linha
      width: Math.min(edge.weight || 1, 5),
      color: (edge.weight || 1) > 2 ? 'rgba(239, 68, 68, 0.4)' : 'rgba(148, 163, 184, 0.2)'
    }));

    return { nodes, links };
  }, [selectedNetwork]);

  useEffect(() => {
    if (networks.length > 0 && !selectedNetwork) {
      setSelectedNetwork(networks[0]); // Auto-seleciona a rede mais recente
    }
  }, [networks, selectedNetwork]);

  const handleUnlock = async () => {
    // Stress Test Bypass (Already unlocked in useEffect)
    setUnlocked(true);
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden relative">
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2 uppercase">
            <NetworkIcon className="w-5 h-5 text-brand-primary" />
            Constelação de Ameaças
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Mapeamento de Redes Coordenadas e Botnets</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-full">
          <Share2 className="w-3.5 h-3.5 text-brand-primary" />
          <span className="text-[10px] font-bold text-brand-primary uppercase">Módulo NetworkX Ativo</span>
        </div>
      </div>

      <div className="relative p-6 flex flex-col lg:flex-row gap-6 bg-bg-main/10">
        
        {/* Painel Lateral: Lista de Redes Detectadas */}
        <div className="w-full lg:w-1/3 flex flex-col gap-4">
          <div className="text-[10px] font-black text-text-muted uppercase tracking-widest border-b border-border-main pb-2">
            Clusters Identificados ({networks.length})
          </div>
          
          <div className="flex-1 overflow-y-auto max-h-[500px] space-y-3 custom-scrollbar pr-2">
            {isLoading ? (
              <div className="text-center py-10 text-text-muted animate-pulse font-mono text-[10px] uppercase">
                Analisando Grafo de Relações...
              </div>
            ) : networks.length === 0 ? (
              <div className="text-center py-10 text-text-muted font-mono text-[10px] uppercase">
                Nenhum ataque coordenado detectado na janela recente.
              </div>
            ) : (
              networks.map((n) => (
                <div 
                  key={n.id} 
                  onClick={() => setSelectedNetwork(n)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedNetwork?.id === n.id ? 'bg-brand-primary/10 border-brand-primary/40' : 'bg-bg-card border-border-main hover:border-brand-primary/20'}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-black text-text-main text-sm tracking-tight">{n.nome_rede}</div>
                    <Badge className="bg-red-500/10 text-red-500 border border-red-500/20 text-[8px] font-black uppercase shadow-none px-1.5 py-0">
                      Score: {n.score_perigoso || 0}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <div className="flex items-center gap-1.5">
                      <Users className="w-3 h-3 text-text-muted" />
                      <span className="text-[10px] text-text-muted font-mono">{n.nodes?.length || 0} Nós</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Globe className="w-3 h-3 text-text-muted" />
                      <span className="text-[10px] text-text-muted font-mono">{n.tipo_coordenacao === 'MULTI_TARGET' ? 'Multi-Alvo' : 'Foco Único'}</span>
                    </div>
                  </div>
                  
                  <div className="text-[8px] text-text-muted font-mono mt-3 uppercase tracking-wider opacity-60">
                    Detectado: {new Date(n.created_at).toLocaleString('pt-BR')}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Visualizador do Grafo (Force Graph) */}
        <div className="w-full lg:w-2/3 h-[500px] border border-border-main rounded-xl relative overflow-hidden bg-[#0f172a] shadow-inner">
           {selectedNetwork ? (
             <>
               <div className="absolute top-4 left-4 z-10 bg-bg-card/80 backdrop-blur border border-border-main p-3 rounded-lg pointer-events-none">
                  <div className="text-xs font-black text-white uppercase tracking-wider mb-1">{selectedNetwork.nome_rede}</div>
                  <div className="text-[9px] text-slate-400 font-mono">Zoom habilitado • Arraste os nós para interagir</div>
                  <div className="mt-3 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#ef4444]" />
                      <span className="text-[8px] text-slate-300 uppercase font-bold">Atacante Multi-Alvo</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                      <span className="text-[8px] text-slate-300 uppercase font-bold">Atacante Padrão</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-[#3b82f6]" />
                      <span className="text-[8px] text-slate-300 uppercase font-bold">Alvo / Vítima</span>
                    </div>
                  </div>
               </div>
               
               <ForceGraphWrapper 
                  graphData={graphData} 
                  onNodeClick={(node) => {
                     // Interação futura: ao clicar no nó, abrir drawer lateral com detalhes
                     console.log("Node clicked", node);
                  }}
               />
             </>
           ) : (
             <div className="w-full h-full flex items-center justify-center text-slate-500 font-mono text-[10px] uppercase tracking-widest">
               Selecione um cluster para renderizar
             </div>
           )}
        </div>

        {/* Lock Overlay (Beta Bypass Ativo) */}
        {!unlocked && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-bg-card/40 backdrop-blur-[2px]">
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
                [BETA] Desbloquear Acesso Gratuito
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 bg-bg-main/30 border-t border-border-main flex justify-between items-center text-[10px] text-text-muted uppercase tracking-widest font-medium">
        <span>Engenharia de Grafos Ativa</span>
        <span>Renderização Acelerada (Canvas 2D)</span>
      </div>
    </div>
  );
}
