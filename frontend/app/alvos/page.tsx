'use client';

import TargetsTab from "@/components/warroom/TargetsTab";
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export default function AlvosPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="border-b border-border-main pb-6">
        <h1 className="text-4xl font-black text-text-main tracking-tighter uppercase">Central de Candidatos</h1>
        <p className="text-text-muted mt-2 leading-relaxed max-w-2xl">
          Gerenciamento e radar de alvos ativos no monitoramento. Acompanhe o score de risco e a volumetria de cada perfil sob observação cívica.
        </p>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          <TargetsTab />
          {/* Anúncio AdSense */}
          <AdSenseSlot adSlot="2020882637" format="vertical" />
      </div>
    </div>
  );
}
