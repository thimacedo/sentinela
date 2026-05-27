"use client";

import { useEffect, useRef } from 'react';

type AdSenseSlotProps = {
  /** ID da unidade de anúncio criada no Google AdSense */
  adSlot: string;
  /** Formato do bloco: horizontal (728×90), vertical (300×250) ou auto */
  format?: 'horizontal' | 'vertical' | 'auto';
};

/**
 * Componente reutilizável que rende um bloco de anúncios do Google AdSense.
 * O script `adsbygoogle.js` já é carregado globalmente no layout.
 * Ao montar, o componente dispara `adsbygoogle.push()` para solicitar a
 * renderização do anúncio.
 */
export default function AdSenseSlot({ adSlot, format = 'auto' }: AdSenseSlotProps) {
  const insRef = useRef<HTMLModElement>(null);

  useEffect(() => {
    // Garantir que o script já está disponível antes de chamar push
    if (typeof window !== 'undefined' && (window as any).adsbygoogle) {
      // @ts-ignore – a lib cria a função global
      (window as any).adsbygoogle.push({});
    }
  }, []);

  // Dimensões padrão baseadas no formato escolhido
  const dimensions =
    format === 'horizontal'
      ? { width: 728, height: 90 }
      : format === 'vertical'
      ? { width: 300, height: 250 }
      : { width: 'auto', height: 'auto' };

  return (
    <div className="my-6 flex justify-center">
      <ins
        ref={insRef}
        className="adsbygoogle"
        style={{
          display: 'block',
          width: dimensions.width as any,
          height: dimensions.height as any,
        }}
        data-ad-client="ca-pub-1827611269042960"
        data-ad-slot={adSlot}
        data-ad-format={format}
      />
    </div>
  );
}
