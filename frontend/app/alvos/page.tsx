'use client';

import TargetsTab from "@/components/warroom/TargetsTab";
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export default function AlvosPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">Central de Candidatos</h1>
          <p className="text-xs text-text-muted mt-1">
            Gerenciamento e radar de alvos ativos no monitoramento. Acompanhe o score de risco.
          </p>
        </div>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          <TargetsTab />
          {/* Anúncio AdSense */}
          <AdSenseSlot adSlot="2020882637" format="vertical" />
      </div>
    </div>
  );
}
