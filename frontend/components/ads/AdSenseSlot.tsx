"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import { useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';

type AdSenseSlotProps = {
  /** ID da unidade de anúncio criada no Google AdSense */
  adSlot: string;
  /** Identificador opcional da instância na página para evitar colisão de keys no SPA */
  slotId?: string;
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
 * Suporta Native, In-Feed, In-Article e Multiplex, com detecção e autocura para AdBlock.
 */
export default function AdSenseSlot({ adSlot, slotId, format = 'auto', layout, layoutKey, style }: AdSenseSlotProps) {
  const insRef = useRef<HTMLModElement>(null);
  const pathname = usePathname();
  const [isBlocked, setIsBlocked] = useState(false);

  useEffect(() => {
    let retries = 0;
    let timer: NodeJS.Timeout;

    const tryLoadAd = () => {
      try {
        if (typeof window === 'undefined') return;
        if (!insRef.current || insRef.current.hasAttribute('data-adsbygoogle-status')) return;

        const hasScript = !!document.querySelector('script[src*="adsbygoogle.js"]');
        if (!hasScript || typeof (window as any).adsbygoogle === 'undefined') {
          if (retries < 8) {
            retries += 1;
            timer = setTimeout(tryLoadAd, 500);
          }
          return;
        }

        (window as any).adsbygoogle.push({});
      } catch (err) {
        console.warn("⚠️ AdSense injeção falhou silenciosamente:", err);
      }
    };

    timer = setTimeout(tryLoadAd, 500);
    setIsBlocked(false);

    return () => {
      clearTimeout(timer);
      // Evita o vazamento de pushes pendentes (desalinhamento em SPAs com internet lenta)
      if (typeof window !== 'undefined' && Array.isArray((window as any).adsbygoogle)) {
        const arr = (window as any).adsbygoogle;
        const idx = arr.indexOf({});
        if (idx > -1) {
          arr.splice(idx, 1);
        } else if (arr.length > 0) {
          arr.pop();
        }
      }
    };
  }, [pathname, adSlot]);

  // Detecção ativa de AdBlocker / Falha de Injeção
  useEffect(() => {
    const checkTimer = setTimeout(() => {
      if (insRef.current) {
        // Se o Google não inseriu nenhum elemento filho dentro do <ins> (iframe do anúncio),
        // significa que o script falhou ou foi interceptado por um AdBlocker.
        if (insRef.current.children.length === 0) {
          setIsBlocked(true);
        }
      }
    }, 4000);

    return () => clearTimeout(checkTimer);
  }, [pathname, adSlot]);

  if (isBlocked) {
    // Esconde o container completamente para evitar lacunas vazias e buracos estéticos no layout
    return null;
  }

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
        key={pathname + '-' + adSlot + (slotId ? '-' + slotId : '')}
        className="adsbygoogle z-10 w-full"
        style={{ display: 'block', ...style }}
        data-ad-client={process.env.NEXT_PUBLIC_ADSENSE_ID || "ca-pub-1827611269042960"}
        data-ad-slot={adSlot}
        data-ad-format={format}
        data-ad-layout={layout}
        data-ad-layout-key={layoutKey}
        data-full-width-responsive={isNative ? undefined : "true"}
      />
    </div>
  );
}
