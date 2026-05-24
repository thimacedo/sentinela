'use client';

import WarRoomOverview from "@/components/warroom/WarRoomOverview";

export default function WarRoom() {
  return (
    <div className="max-w-7xl mx-auto space-y-10">
      {/* Page Header */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800 pb-8">
        <div>
          <p className="text-emerald-500 font-mono text-xs uppercase tracking-widest mb-2 font-semibold">
            Status: Operacional
          </p>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">
            Panorama <span className="text-slate-500">Operacional</span>
          </h1>
        </div>
        <div className="text-left md:text-right">
          <div className="text-[11px] font-mono text-slate-500 leading-tight">
            SISTEMA SENTINELA // <span className="text-slate-400">PASA v54.0</span>
          </div>
          <div className="text-[10px] font-mono text-slate-600 uppercase tracking-wider mt-1">
            Módulo de Inteligência em Tempo Real
          </div>
        </div>
      </header>
      
      <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <WarRoomOverview />
      </section>
    </div>
  );
}
