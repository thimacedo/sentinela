'use client';

import ForensicTab from "@/components/warroom/ForensicTab";

export default function PericiaPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="border-b border-border-main pb-6">
        <h1 className="text-4xl font-black text-text-main tracking-tighter uppercase">Análise Pericial</h1>
        <p className="text-text-muted mt-2 leading-relaxed max-w-2xl">
          Exploração técnica e detalhada dos comentários processados pela nossa inteligência artificial. 
          Acompanhe os marcadores linguísticos e o score de confiança forense.
        </p>
      </div>
      
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <ForensicTab />
      </div>
    </div>
  );
}
