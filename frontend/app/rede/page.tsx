'use client';

import NetworkTab from "@/components/warroom/NetworkTab";

export default function RedePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter uppercase">Análise de Rede</h1>
      <NetworkTab />
    </div>
  );
}
