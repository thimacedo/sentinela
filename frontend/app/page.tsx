'use client';

import WarRoomOverview from "@/components/warroom/WarRoomOverview";

export default function WarRoom() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter">PANORAMA OPERACIONAL</h1>
        <div className="text-right">
          <div className="text-[10px] font-mono text-tactical-accent/60 leading-none">
            SISTEMA SENTINELA // PASA v52.4
          </div>
          <div className="text-[8px] font-mono text-gray-500 uppercase tracking-widest mt-1">
            Central de Comando Operacional
          </div>
        </div>
      </div>
      
      <WarRoomOverview />
    </div>
  );
}
