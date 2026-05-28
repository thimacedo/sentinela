'use client';

import DossiersTab from "@/components/warroom/DossiersTab";
import AdSenseSlot from "@/components/ads/AdSenseSlot";

export default function DossiesPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="border-b border-border-main pb-6">
        <h1 className="text-4xl font-black text-text-main tracking-tighter uppercase">Emissão de Relatórios</h1>
        <p className="text-text-muted mt-2 leading-relaxed max-w-2xl">
          Consolidação de evidências e métricas em documentos técnicos (PDF). 
          Cada dossiê contém o histórico completo de detecções e análises para um alvo específico.
        </p>
      </div>

      <AdSenseSlot adSlot="2020882637" format="horizontal" />

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <DossiersTab />
      </div>
    </div>
  );
}
