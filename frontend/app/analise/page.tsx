'use client';

import { Suspense } from "react";
import AnaliseTab from "@/components/warroom/AnaliseTab";
import AdSenseSlot from "@/components/ads/AdSenseSlot";
import { Loader2 } from "lucide-react";

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
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center py-32 text-text-muted gap-4 bg-bg-card border border-border-main rounded-2xl">
            <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
            <span className="animate-pulse font-mono text-[10px] uppercase tracking-widest">Carregando Módulos de Análise...</span>
          </div>
        }>
          <AnaliseTab />
        </Suspense>
        <div className="mt-8">
          <AdSenseSlot adSlot="2020882637" format="horizontal" />
        </div>
      </div>
    </div>
  );
}
