'use client';

import AnaliseTab from "@/components/warroom/AnaliseTab";

export default function AnalisePage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="border-b border-border-main pb-6">
        <h1 className="text-4xl font-black text-text-main tracking-tighter uppercase">Análise Avançada</h1>
        <p className="text-text-muted mt-2 leading-relaxed max-w-2xl">
          Exploração técnica e detalhada dos comentários processados pela nossa inteligência artificial. 
          Acompanhe os marcadores linguísticos e o score de confiança técnica.
        </p>
      </div>
      
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <AnaliseTab />
      </div>
    </div>
  );
}
