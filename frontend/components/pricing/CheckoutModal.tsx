'use client';

import React, { useState, useMemo } from 'react';
import { X, Copy, Check, QrCode, ShieldCheck, HelpCircle, CreditCard, ArrowRight, Loader2 } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { generatePixPayload } from '@/lib/pix';

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  planName: string;
  ciAmount: string;
  price: string;
}

export default function CheckoutModal({ isOpen, onClose, planName, ciAmount, price }: CheckoutModalProps) {
  const [copied, setCopied] = useState(false);
  const [loadingStripe, setLoadingStripe] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'pix' | 'card'>('pix');
  
  // Calcula preço numérico e desconto de 5% para o PIX Direto
  const numericPrice = useMemo(() => parseFloat(price.replace('.', '').replace(',', '.')), [price]);
  const pixDiscountedPrice = numericPrice * 0.95;
  
  const pixPayload = useMemo(() => {
    return generatePixPayload('809e630a-97b0-4bbe-902a-1ea5181235e0', pixDiscountedPrice, 'SENTINELA', 'BRASILIA');
  }, [pixDiscountedPrice]);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(pixPayload);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const handleStripeCheckout = async () => {
    try {
      setLoadingStripe(true);
      // Mapeia o nome do plano para o slug do backend
      const slugMap: Record<string, string> = {
        'Operação Tática': 'tatica',
        'War Room': 'warroom',
        'Escala Nacional': 'nacional'
      };
      
      const packageSlug = slugMap[planName] || 'tatica';
      const userId = localStorage.getItem('sentinela_user_id') || 'guest_user';

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/checkout/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, package_slug: packageSlug })
      });
      
      if (!response.ok) throw new Error('Falha ao gerar sessão de pagamento');
      
      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      console.error(error);
      alert('Erro ao conectar com a rede de pagamentos segura. Tente novamente mais tarde.');
    } finally {
      setLoadingStripe(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Box */}
      <div className="relative w-full max-w-md max-h-[90vh] flex flex-col bg-bg-card border border-border-main rounded-3xl shadow-2xl overflow-hidden transform transition-all">
        {/* Header */}
        <div className="bg-bg-main p-6 border-b border-border-main flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-primary/10 rounded-xl flex items-center justify-center border border-brand-primary/20">
              <ShieldCheck className="w-5 h-5 text-brand-primary" />
            </div>
            <div>
              <h3 className="text-lg font-black text-text-main tracking-tight leading-none">Gateway Seguro</h3>
              <p className="text-[10px] text-text-muted font-mono uppercase tracking-widest mt-1">Transação Criptografada</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-full text-text-muted hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
          {/* Formas de Pagamento (Abas) */}
          <div className="flex p-1 bg-bg-main rounded-lg mb-6 border border-border-main">
            <button 
              onClick={() => setPaymentMethod('pix')}
              className={`flex-1 py-2 text-xs font-bold uppercase tracking-widest rounded-md transition-all flex items-center justify-center gap-2 ${paymentMethod === 'pix' ? 'bg-bg-card text-brand-primary shadow-sm border border-border-main' : 'text-text-muted hover:text-text-main'}`}
            >
              <QrCode className="w-4 h-4" /> PIX (5% OFF)
            </button>
            <button 
              onClick={() => setPaymentMethod('card')}
              className={`flex-1 py-2 text-xs font-bold uppercase tracking-widest rounded-md transition-all flex items-center justify-center gap-2 ${paymentMethod === 'card' ? 'bg-bg-card text-brand-primary shadow-sm border border-border-main' : 'text-text-muted hover:text-text-main'}`}
            >
              <CreditCard className="w-4 h-4" /> Cartão / Stripe
            </button>
          </div>

          {/* Order Summary */}
          <div className="mb-6 p-4 bg-bg-main border border-border-main rounded-xl flex justify-between items-center">
            <div>
              <p className="text-xs text-text-muted uppercase tracking-widest font-bold mb-1">Aporte Estratégico</p>
              <p className="text-sm font-black text-text-main">{planName}</p>
              <p className="text-xs text-brand-primary font-mono mt-0.5">+{ciAmount} CI</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-text-muted uppercase tracking-widest font-bold mb-1">
                {paymentMethod === 'pix' ? 'Valor com Desconto' : 'Valor Total'}
              </p>
              {paymentMethod === 'pix' ? (
                <>
                  <p className="text-[10px] text-text-muted line-through mb-0.5 font-mono">R$ {price}</p>
                  <p className="text-2xl font-black text-emerald-500 font-mono">
                    R$ {pixDiscountedPrice.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </>
              ) : (
                <p className="text-2xl font-black text-text-main font-mono">R$ {price}</p>
              )}
            </div>
          </div>

          {paymentMethod === 'pix' ? (
            <div className="flex flex-col items-center animate-in fade-in duration-300">
              <h4 className="text-sm font-bold text-text-main mb-4 uppercase tracking-widest">Escaneie o QR Code</h4>
              
              <div className="bg-white p-2 rounded-2xl mb-6 shadow-inner border-4 border-bg-main">
                <div className="relative w-48 h-48 flex items-center justify-center">
                  <QRCodeSVG 
                    value={pixPayload} 
                    size={192} 
                    level="M"
                    includeMargin={false}
                  />
                </div>
              </div>

              <div className="w-full">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Ou utilize o PIX Copia e Cola</p>
                  <div className="flex items-center gap-1 text-[10px] text-emerald-500 font-mono">
                    <ShieldCheck className="w-3 h-3" /> Nubank Direto
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-2">
                  <input 
                    type="text" 
                    readOnly 
                    value={pixPayload}
                    className="flex-1 bg-bg-main border border-border-main rounded-lg px-4 py-3 text-xs font-mono text-text-main focus:outline-none focus:border-brand-primary/50 text-center truncate"
                  />
                  <button 
                    onClick={handleCopy}
                    className={`px-4 py-3 rounded-lg border font-black uppercase text-[10px] tracking-widest transition-all flex items-center justify-center min-w-[120px] ${
                      copied 
                        ? 'bg-emerald-500 border-emerald-400 text-white shadow-lg shadow-emerald-500/20' 
                        : 'bg-brand-primary border-brand-primary text-white hover:bg-brand-primary/90'
                    }`}
                  >
                    {copied ? (
                      <><Check className="w-4 h-4 mr-1.5" /> Copiado</>
                    ) : (
                      <><Copy className="w-4 h-4 mr-1.5" /> Copiar</>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col animate-in fade-in duration-300 py-4">
              <div className="bg-brand-primary/5 border border-brand-primary/20 rounded-xl p-5 mb-6">
                <div className="flex items-start gap-3">
                  <CreditCard className="w-5 h-5 text-brand-primary shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-bold text-text-main mb-1">Processamento Stripe</h4>
                    <p className="text-xs text-text-muted leading-relaxed">
                      Você será redirecionado para a infraestrutura global da Stripe. Suporta todos os cartões de crédito e PIX oficial.
                    </p>
                  </div>
                </div>
              </div>

              <button 
                onClick={handleStripeCheckout}
                disabled={loadingStripe}
                className="w-full py-4 rounded-xl bg-brand-primary text-white hover:bg-brand-primary/90 transition-all text-sm font-black uppercase tracking-widest shadow-lg shadow-brand-primary/20 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {loadingStripe ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Conectando ao Gateway...</>
                ) : (
                  <>Ir para Pagamento <ArrowRight className="w-5 h-5" /></>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="bg-brand-primary/5 border-t border-brand-primary/10 p-4 flex items-start gap-3 shrink-0">
          <HelpCircle className="w-5 h-5 text-brand-primary shrink-0 mt-0.5" />
          <p className="text-[10px] text-text-muted leading-relaxed font-mono">
            Após a confirmação do pagamento, os <strong className="text-text-main">Créditos de Inteligência (CI)</strong> serão depositados automaticamente na sua conta em até 2 minutos, liberando acesso às varreduras táticas.
          </p>
        </div>
      </div>
    </div>
  );
}
