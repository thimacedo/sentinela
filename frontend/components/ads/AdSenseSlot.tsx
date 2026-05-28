"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

type AdSenseSlotProps = {
  /** ID da unidade de anúncio criada no Google AdSense */
  adSlot: string;
  /** Formato do bloco: horizontal (728×90), vertical (300×250) ou auto */
  format?: 'horizontal' | 'vertical' | 'auto';
};

/**
 * Componente reutilizável que renderiza um bloco de anúncios do Google AdSense.
 * Altamente resiliente a transições de páginas em Next.js (SPA) e StrictMode do React.
 */
export default function AdSenseSlot({ adSlot, format = 'auto' }: AdSenseSlotProps) {
  const insRef = useRef<HTMLModElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    const loadAd = () => {
      try {
        if (typeof window !== 'undefined') {
          // Inicializa a fila global do AdSense se necessário
          (window as any).adsbygoogle = (window as any).adsbygoogle || [];
          
          // Verifica se o elemento ins atual existe e ainda não foi processado pelo AdSense
          if (insRef.current && !insRef.current.hasAttribute('data-adsbygoogle-status')) {
            (window as any).adsbygoogle.push({});
          }
        }
      } catch (err) {
        console.warn("⚠️ AdSense injeção falhou silenciosamente (esperado em ambiente de dev):", err);
      }
    };

    // Pequeno atraso para garantir o desenho do DOM antes do cálculo do layout pelo AdSense
    const timer = setTimeout(loadAd, 200);
    return () => clearTimeout(timer);
  }, [pathname, adSlot]); // Recarrega se mudar a rota ou o slot do bloco

  // Dimensões padrão baseadas no formato escolhido
  const dimensions =
    format === 'horizontal'
      ? { width: 728, height: 90 }
      : format === 'vertical'
      ? { width: 300, height: 250 }
      : { width: 'auto', height: 'auto' };

  return (
    <div className="my-6 flex justify-center w-full overflow-hidden">
      <ins
        ref={insRef}
        className="adsbygoogle"
        style={{
          display: 'block',
          width: dimensions.width as any,
          height: dimensions.height as any,
          margin: '0 auto',
        }}
        data-ad-client="ca-pub-1827611269042960"
        data-ad-slot={adSlot}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
}
