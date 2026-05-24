'use client';

import NetworkTab from "@/components/warroom/NetworkTab";

export default function RedePage() {
  return (
    <div className="max-w-7xl mx-auto space-y-10 opacity-60 pointer-events-none select-none relative">
      {/* Overlay de Congelamento */}
      <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto">
        <div className="bg-slate-900 border border-emerald-500/30 p-8 rounded-xl shadow-2xl text-center space-y-5 max-w-md mx-4 backdrop-blur-md">
          <div className="w-14 h-14 bg-emerald-500/10 text-emerald-500 rounded-full flex items-center justify-center mx-auto animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"></path><path d="M12 5v14"></path></svg>
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white uppercase tracking-tight">Análise de Rede</h2>
            <p className="text-emerald-500 font-mono text-[10px] uppercase tracking-[0.2em]">Módulo em Calibração</p>
          </div>
          <p className="text-slate-400 text-sm leading-relaxed">
            O mapeamento de conexões coordenadas e grafos de influência está sendo processado pela nova engine de IA. 
            Os dados estarão disponíveis após a conclusão do ciclo de treinamento.
          </p>
        </div>
      </div>

      <div className="space-y-6 filter blur-md">
        <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter uppercase">Análise de Rede</h1>
        <NetworkTab />
      </div>
    </div>
  );
}
