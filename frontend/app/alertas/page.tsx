'use client';

import AlertsTab from "@/components/warroom/AlertsTab";

export default function AlertasPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      <div className="border-b border-border-main pb-6">
        <h1 className="text-4xl font-black text-text-main tracking-tighter uppercase">Central de Alertas</h1>
        <p className="text-text-muted mt-2 leading-relaxed max-w-2xl">
          Monitoramento crítico de incidentes de hostilidade e ataques coordenados. 
          Cada alerta representa um pulso de atividade que requer atenção técnica.
        </p>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <AlertsTab />
      </div>
    </div>
  );
}
