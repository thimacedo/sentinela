'use client';

import AlertsTab from "@/components/warroom/AlertsTab";

export default function AlertasPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter uppercase">Central de Alertas</h1>
      <AlertsTab />
    </div>
  );
}
