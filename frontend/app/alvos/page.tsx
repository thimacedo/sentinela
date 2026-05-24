'use client';

import TargetsTab from "@/components/warroom/TargetsTab";

export default function AlvosPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter uppercase">Monitoramento de Alvos</h1>
      <TargetsTab />
    </div>
  );
}
