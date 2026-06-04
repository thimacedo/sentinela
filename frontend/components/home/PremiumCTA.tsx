'use client';
/* eslint-disable @typescript-eslint/no-unused-vars */

import React from 'react';
import { useRouter } from 'next/navigation';

export default function PremiumCTA() {
  const router = useRouter();

  return (
    <div className="bg-bg-card border-2 border-brand-primary p-8 rounded-[2rem] text-center shadow-2xl relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary/5 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-1000" />
      <div className="relative z-10">
        <div className="text-3xl mb-4">💎</div>
        <h3 className="text-xl font-bold mb-2 tracking-tight text-text-main">Inteligência Ilimitada</h3>
        <p className="text-text-muted text-xs mb-8 leading-relaxed">
          Dossiês completos, análise de grafos de influência e relatórios em tempo real com validade técnica.
        </p>
        <div className="space-y-3">
          <button onClick={() => router.push('/planos')} className="w-full bg-brand-primary text-white py-4 rounded-2xl font-black text-xs uppercase tracking-widest shadow-lg shadow-brand-primary/10 hover:translate-y-[-2px] transition-all active:scale-95">
            Adquirir Créditos de Inteligência
          </button>
          <p className="text-[9px] text-text-muted font-bold uppercase tracking-widest">
            Opere na rede a partir de 1.000 CI
          </p>
        </div>
      </div>
    </div>
  );
}
