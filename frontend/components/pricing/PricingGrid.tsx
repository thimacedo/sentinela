'use client';

import { useState, useEffect } from 'react';
import CheckoutModal from './CheckoutModal';
import { Check, ShieldAlert, Zap, Timer } from 'lucide-react';

export default function PricingGrid() {
  const [timeLeft, setTimeLeft] = useState(899); // 14:59
  const [checkoutModal, setCheckoutModal] = useState<{isOpen: boolean, planName: string, ciAmount: string, price: string}>({
    isOpen: false, planName: '', ciAmount: '', price: ''
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleCheckout = (planName: string, ciAmount: string, price: string) => {
    setCheckoutModal({ isOpen: true, planName, ciAmount, price });
  };

  return (
    <div className="w-full">
      <CheckoutModal 
        isOpen={checkoutModal.isOpen} 
        onClose={() => setCheckoutModal({ ...checkoutModal, isOpen: false })} 
        planName={checkoutModal.planName}
        ciAmount={checkoutModal.ciAmount}
        price={checkoutModal.price}
      />
      {/* Banner de Status do Sistema */}
      <div className="bg-brand-primary/10 border border-brand-primary/20 rounded-xl p-4 mb-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-brand-primary animate-pulse" />
          <p className="text-sm font-bold text-text-main">
            Operação em Malha de Inteligência PASA v86.0 Ativa
          </p>
        </div>
        <div className="bg-bg-main px-4 py-2 rounded-lg border border-border-main flex items-center gap-2 shadow-inner">
          <span className="text-xs text-text-muted font-mono uppercase tracking-widest text-[9px]">Sincronização via Supabase</span>
          <span className="text-lg font-black text-brand-primary font-mono tabular-nums">99.9%</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Tier 1: Operação Tática */}
        <div className="bg-bg-card border border-border-main rounded-2xl p-8 flex flex-col hover:border-brand-primary/30 transition-all shadow-sm group">
          <div className="mb-6">
            <h3 className="text-lg font-black text-text-main uppercase tracking-widest mb-2 group-hover:text-brand-primary transition-colors">Operação Tática</h3>
            <p className="text-xs text-text-muted leading-relaxed">Capacidade básica para monitoramento pontual e auditoria de alvos específicos.</p>
          </div>
          
          <div className="mb-6 pb-6 border-b border-border-main">
            <div className="flex items-end gap-2 text-text-main font-mono">
              <span className="text-4xl font-black tracking-tighter text-text-main">1.000</span>
              <span className="text-sm font-bold text-brand-primary mb-1">CI</span>
            </div>
            <p className="text-[10px] text-text-muted uppercase tracking-widest mt-2 font-bold">Investimento: R$ 497</p>
          </div>

          <ul className="space-y-4 mb-8 flex-1">
            <li className="flex items-start gap-3 text-xs text-text-main">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Geração de até 3 Dossiês Estratégicos com selo de integridade.</span>
            </li>
            <li className="flex items-start gap-3 text-xs text-text-main">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Injeção de até 2 novos alvos na malha de coleta.</span>
            </li>
          </ul>

          <button onClick={() => handleCheckout('Operação Tática', '1.000', '497,00')} className="w-full py-4 rounded-xl border border-border-main bg-bg-main hover:bg-brand-primary/10 hover:border-brand-primary hover:text-brand-primary transition-all text-[10px] font-black uppercase tracking-widest text-text-main shadow-sm">
            Autorizar Aporte Tático
          </button>
        </div>

        {/* Tier 2: War Room */}
        <div className="bg-bg-card border-2 border-brand-primary rounded-2xl p-8 flex flex-col relative shadow-xl transform md:-translate-y-4">
          <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-brand-primary text-white px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg flex items-center gap-1.5">
            <Zap className="w-3 h-3 fill-white" /> Escolha Estratégica
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-black text-brand-primary uppercase tracking-widest mb-2">War Room</h3>
            <p className="text-xs text-text-muted leading-relaxed">Arsenal completo para gestão de crises agudas e monitoramento de campanhas majoritárias.</p>
          </div>
          
          <div className="mb-6 pb-6 border-b border-border-main font-mono">
            <div className="flex flex-col">
              <div className="flex items-end gap-2 text-text-main">
                <span className="text-5xl font-black tracking-tighter">6.000</span>
                <span className="text-sm font-bold text-brand-primary mb-1">CI</span>
              </div>
              <div className="text-[9px] font-bold text-emerald-500 mt-2 bg-emerald-500/10 inline-block px-2 py-1 rounded border border-emerald-500/20 uppercase tracking-widest">
                Inclui +1.000 CI de Bônus Beta
              </div>
            </div>
            <p className="text-[10px] text-text-muted uppercase tracking-widest mt-4 font-bold">Investimento: R$ 1.997</p>
          </div>

          <ul className="space-y-4 mb-8 flex-1">
            <li className="flex items-start gap-3 text-xs text-text-main">
              <Check className="w-4 h-4 text-brand-primary mt-0.5 shrink-0" />
              <span>Acesso ao Radar de Redes Coordenadas (Clusters).</span>
            </li>
            <li className="flex items-start gap-3 text-xs text-text-main">
              <Check className="w-4 h-4 text-brand-primary mt-0.5 shrink-0" />
              <span>Prioridade de processamento no AI-Processor (Mistral/Groq).</span>
            </li>
            <li className="flex items-start gap-3 text-xs text-text-main">
              <Check className="w-4 h-4 text-brand-primary mt-0.5 shrink-0" />
              <span>Exportação ilimitada de Dossiês de Análise durante o período.</span>
            </li>
          </ul>

          <button onClick={() => handleCheckout('War Room', '6.000', '1.997,00')} className="w-full py-4 rounded-xl bg-brand-primary text-white hover:bg-brand-primary/90 transition-all text-[10px] font-black uppercase tracking-widest shadow-lg shadow-brand-primary/20">
            Ativar War Room Imediato
          </button>
        </div>

        {/* Tier 3: Escala Nacional */}
        <div className="bg-bg-card border border-border-main rounded-2xl p-8 flex flex-col hover:border-brand-primary/30 transition-all shadow-sm group">
          <div className="mb-6">
            <h3 className="text-lg font-black text-text-main uppercase tracking-widest mb-2 group-hover:text-brand-primary transition-colors">Escala Nacional</h3>
            <p className="text-xs text-text-muted leading-relaxed">Controle total de inteligência para diretórios estaduais ou agências de monitoramento global.</p>
          </div>
          
          <div className="mb-6 pb-6 border-b border-border-main font-mono">
            <div className="flex items-end gap-2 text-text-main">
              <span className="text-4xl font-black tracking-tighter font-mono">25.000</span>
              <span className="text-sm font-bold text-brand-primary mb-1 font-sans">CI</span>
            </div>
            <p className="text-[10px] text-text-muted uppercase tracking-widest mt-2 font-bold tracking-tighter">Investimento: R$ 7.997</p>
          </div>

          <ul className="space-y-4 mb-8 flex-1 text-xs">
            <li className="flex items-start gap-3 text-text-main">
              <ShieldAlert className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
              <span className="font-bold">Capacidade de monitorar até 500 alvos simultâneos.</span>
            </li>
            <li className="flex items-start gap-3 text-text-main">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Acesso ao motor de perícia forense com Triagem Local.</span>
            </li>
          </ul>

          <button onClick={() => handleCheckout('Escala Nacional', '25.000', '7.997,00')} className="w-full py-4 rounded-xl border border-border-main bg-bg-main hover:bg-brand-primary/10 hover:border-brand-primary hover:text-brand-primary transition-all text-[10px] font-black uppercase tracking-widest text-text-main shadow-sm">
            Solicitar Aporte Nacional
          </button>
        </div>
      </div>
    </div>
  );
}
