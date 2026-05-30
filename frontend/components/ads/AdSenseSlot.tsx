"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

type AdSenseSlotProps = {
  /** ID da unidade de anúncio criada no Google AdSense */
  adSlot: string;
  /** Formato do bloco */
  format?: 'horizontal' | 'vertical' | 'auto' | 'fluid' | 'autorelaxed';
  /** Layout para anúncios in-article ou específicos */
  layout?: 'in-article' | string;
  /** Layout key para anúncios in-feed nativos */
  layoutKey?: string;
  /** Estilos inline customizados */
  style?: React.CSSProperties;
};

/**
 * Componente reutilizável que renderiza um bloco de anúncios do Google AdSense.
 * Altamente resiliente a transições de páginas em Next.js (SPA) e StrictMode do React.
 * Suporta Native, In-Feed, In-Article e Multiplex.
 */
export default function AdSenseSlot({ adSlot, format = 'auto', layout, layoutKey, style }: AdSenseSlotProps) {
  const insRef = useRef<HTMLModElement>(null);
  const pathname = usePathname();

  useEffect(() => {
    const loadAd = () => {
      try {
        if (typeof window !== 'undefined') {
          (window as any).adsbygoogle = (window as any).adsbygoogle || [];
          
          if (insRef.current && !insRef.current.hasAttribute('data-adsbygoogle-status')) {
            (window as any).adsbygoogle.push({});
          }
        }
      } catch (err) {
        console.warn("⚠️ AdSense injeção falhou silenciosamente:", err);
      }
    };

    const timer = setTimeout(loadAd, 200);
    return () => clearTimeout(timer);
  }, [pathname, adSlot]);

  // Se format for fluid ou autorelaxed (nativo), não fixamos altura para evitar distorções
  const isNative = format === 'fluid' || format === 'autorelaxed';
  const minHeight = isNative ? undefined : (format === 'horizontal' ? 90 : format === 'vertical' ? 250 : 100);

  return (
    <div 
      className="my-6 w-full flex items-center justify-center bg-transparent relative transition-colors"
      style={{ minHeight: minHeight ? `${minHeight}px` : 'auto' }}
      aria-label="Espaço Publicitário"
    >
      <ins
        ref={insRef}
        key={pathname + '-' + adSlot}
        className="adsbygoogle z-10 w-full"
        style={{ display: 'block', ...style }}
        data-ad-client="ca-pub-1827611269042960"
        data-ad-slot={adSlot}
        data-ad-format={format}
        data-ad-layout={layout}
        data-ad-layout-key={layoutKey}
        data-full-width-responsive={isNative ? undefined : "true"}
      />
    </div>
  );
}
