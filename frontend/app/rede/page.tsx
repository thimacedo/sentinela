'use client';

import NetworkTab from "@/components/warroom/NetworkTab";
import AdSenseSlot from "@/components/ads/AdSenseSlot";

export default function RedePage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="border-b border-border-main pb-6">
        <h1 className="text-4xl font-black text-text-main tracking-tighter uppercase">Análise de Rede</h1>
        <p className="text-text-muted mt-2 leading-relaxed max-w-2xl">
          Mapeamento de comportamentos coordenados e clusters de influência. 
          Identifique redes artificiais e padrões de automação no discurso digital.
        </p>
      </div>

      <AdSenseSlot adSlot="2020882637" format="horizontal" />

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <NetworkTab />
      </div>
    </div>
  );
}
