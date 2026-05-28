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
      {/* FOMO Banner */}
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Timer className="w-5 h-5 text-red-500 animate-pulse" />
          <p className="text-sm font-bold text-red-500">
            Acesso Antecipado aos Clusters Residenciais V2
          </p>
        </div>
        <div className="bg-bg-main px-4 py-2 rounded-lg border border-red-500/30 flex items-center gap-2 shadow-inner">
          <span className="text-xs text-text-muted font-mono uppercase tracking-widest">Bônus Expira Em</span>
          <span className="text-lg font-black text-text-main font-mono">{formatTime(timeLeft)}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Tier 1 */}
        <div className="bg-bg-card border border-border-main rounded-2xl p-8 flex flex-col hover:border-brand-primary/30 transition-all shadow-sm">
          <div className="mb-6">
            <h3 className="text-lg font-black text-text-main uppercase tracking-widest mb-2">Operação Tática</h3>
            <p className="text-xs text-text-muted">Licença básica para monitoramento pontual e verificação de alvos locais.</p>
          </div>
          
          <div className="mb-6 pb-6 border-b border-border-main">
            <div className="flex items-end gap-2">
              <span className="text-4xl font-black text-text-main font-mono">1.000</span>
              <span className="text-sm font-bold text-brand-primary mb-1">CI</span>
            </div>
            <p className="text-[10px] text-text-muted uppercase tracking-widest mt-2">Investimento: R$ 497</p>
          </div>

          <ul className="space-y-4 mb-8 flex-1">
            <li className="flex items-start gap-3 text-sm text-text-main">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Suficiente para ~2 Dossiês ou 6 dias de monitoramento ativo.</span>
            </li>
            <li className="flex items-start gap-3 text-sm text-text-main">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Acesso ao Painel Central.</span>
            </li>
          </ul>

          <button onClick={() => handleCheckout('Operação Tática', '1.000', '497,00')} className="w-full py-4 rounded-xl border border-border-main bg-bg-main hover:bg-brand-primary/10 hover:border-brand-primary hover:text-brand-primary transition-colors text-sm font-black uppercase tracking-widest text-text-main">
            Liberar Acesso Tático
          </button>
        </div>

        {/* Tier 2 (Mais Popular) */}
        <div className="bg-bg-card border-2 border-brand-primary rounded-2xl p-8 flex flex-col relative shadow-xl transform md:-translate-y-4">
          <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-brand-primary text-white px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg flex items-center gap-1.5">
            <Zap className="w-3 h-3 fill-white" /> Recomendado
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-black text-brand-primary uppercase tracking-widest mb-2">War Room</h3>
            <p className="text-xs text-text-muted">Arsenal de inteligência completo para campanhas majoritárias e gestão de crise.</p>
          </div>
          
          <div className="mb-6 pb-6 border-b border-border-main">
            <div className="flex flex-col">
              {timeLeft > 0 && (
                <div className="text-xs font-mono text-emerald-500 font-bold mb-1 line-through opacity-50">+0 CI (Sem Bônus)</div>
              )}
              <div className="flex items-end gap-2">
                <span className="text-5xl font-black text-text-main font-mono">5.000</span>
                <span className="text-sm font-bold text-brand-primary mb-1">CI</span>
              </div>
              {timeLeft > 0 && (
                <div className="text-xs font-mono font-bold text-emerald-500 mt-2 bg-emerald-500/10 inline-block px-2 py-1 rounded border border-emerald-500/20">
                  +1.000 CI BÔNUS TEMPORÁRIO
                </div>
              )}
            </div>
            <p className="text-[10px] text-text-muted uppercase tracking-widest mt-4">Investimento: R$ 1.997</p>
          </div>

          <ul className="space-y-4 mb-8 flex-1">
            <li className="flex items-start gap-3 text-sm text-text-main">
              <Check className="w-4 h-4 text-brand-primary mt-0.5 shrink-0" />
              <span className="font-bold">Acesso Antecipado ao Deep Scrape.</span>
            </li>
            <li className="flex items-start gap-3 text-sm text-text-main">
              <Check className="w-4 h-4 text-brand-primary mt-0.5 shrink-0" />
              <span>Suficiente para monitoramento maciço e investigações cruzadas.</span>
            </li>
            <li className="flex items-start gap-3 text-sm text-text-main">
              <Check className="w-4 h-4 text-brand-primary mt-0.5 shrink-0" />
              <span>Alertas SMS/WhatsApp em Tempo Real.</span>
            </li>
          </ul>

          <button onClick={() => handleCheckout('War Room', '6.000', '1.997,00')} className="w-full py-4 rounded-xl bg-brand-primary text-white hover:bg-brand-primary/90 transition-all text-sm font-black uppercase tracking-widest shadow-lg shadow-brand-primary/20">
            Montar War Room
          </button>
          <p className="text-[9px] text-center text-text-muted mt-3 font-mono uppercase">Apenas 3 Vagas Restantes no Servidor</p>
        </div>

        {/* Tier 3 */}
        <div className="bg-bg-card border border-border-main rounded-2xl p-8 flex flex-col hover:border-brand-primary/30 transition-all shadow-sm">
          <div className="mb-6">
            <h3 className="text-lg font-black text-text-main uppercase tracking-widest mb-2">Escala Nacional</h3>
            <p className="text-xs text-text-muted">Acesso ilimitado de IPs residenciais e suporte de equipe técnica dedicada.</p>
          </div>
          
          <div className="mb-6 pb-6 border-b border-border-main">
            <div className="flex items-end gap-2">
              <span className="text-4xl font-black text-text-main font-mono">25.000</span>
              <span className="text-sm font-bold text-brand-primary mb-1">CI</span>
            </div>
            <p className="text-[10px] text-text-muted uppercase tracking-widest mt-2">Investimento: R$ 7.997</p>
          </div>

          <ul className="space-y-4 mb-8 flex-1">
            <li className="flex items-start gap-3 text-sm text-text-main">
              <ShieldAlert className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
              <span className="font-bold">Prioridade de Processamento MAX.</span>
            </li>
            <li className="flex items-start gap-3 text-sm text-text-main">
              <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <span>Operação em múltiplos alvos e múltiplos diretórios estaduais.</span>
            </li>
          </ul>

          <button onClick={() => handleCheckout('Escala Nacional', '25.000', '7.997,00')} className="w-full py-4 rounded-xl border border-border-main bg-bg-main hover:bg-brand-primary/10 hover:border-brand-primary hover:text-brand-primary transition-colors text-sm font-black uppercase tracking-widest text-text-main">
            Consultar Disponibilidade
          </button>
        </div>
      </div>
    </div>
  );
}
