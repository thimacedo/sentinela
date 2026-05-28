'use client';

import AnaliseTab from "@/components/warroom/AnaliseTab";
import AdSenseSlot from "@/components/ads/AdSenseSlot";

export default function AnalisePage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">Análise Avançada</h1>
          <p className="text-xs text-text-muted mt-1">
            Exploração técnica e detalhada dos comentários processados pela nossa inteligência artificial.
          </p>
        </div>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <AnaliseTab />
        <div className="mt-8">
          <AdSenseSlot adSlot="2020882637" format="horizontal" />
        </div>
      </div>
    </div>
  );
}
