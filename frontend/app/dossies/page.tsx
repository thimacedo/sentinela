'use client';

import DossiersTab from "@/components/warroom/DossiersTab";
import AdSenseSlot from "@/components/ads/AdSenseSlot";

export default function DossiesPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">Emissão de Relatórios</h1>
          <p className="text-xs text-text-muted mt-1">
            Consolidação de indícios e métricas em documentos técnicos (PDF).
          </p>
        </div>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <DossiersTab />
        <div className="mt-8">
          <AdSenseSlot adSlot="2020882637" format="horizontal" />
        </div>
      </div>
    </div>
  );
}
