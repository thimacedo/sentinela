'use client';

import AlertsTab from "@/components/warroom/AlertsTab";
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export default function AlertasPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">Central de Alertas</h1>
          <p className="text-xs text-text-muted mt-1">
            Monitoramento crítico de incidentes de hostilidade e ataques coordenados.
          </p>
        </div>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          <AlertsTab />
          {/* Anúncio AdSense */}
          <AdSenseSlot adSlot="2020882637" format="vertical" />
      </div>
    </div>
  );
}
