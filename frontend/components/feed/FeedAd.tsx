"use client";
import { useEffect } from "react";
import dynamic from "next/dynamic";

/**
 * Componente interno para injeção de anúncio AdSense no Feed.
 */
function AdSenseInner() {
  useEffect(() => {
    try {
      // O push só funciona se o script base do layout.tsx já tiver carregado
      (window as any).adsbygoogle = (window as any).adsbygoogle || [];
      (window as any).adsbygoogle.push({});
    } catch (err) {
      console.error("AdSense error:", err);
    }
  }, []);

  const adsenseId = process.env.NEXT_PUBLIC_ADSENSE_ID || 'ca-pub-1827611269042960';

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl p-4 mb-4 flex flex-col items-center justify-center min-h-[120px] overflow-hidden shadow-sm">
      <span className="text-[8px] font-black text-text-muted uppercase tracking-widest mb-3">Espaço Publicitário</span>
      <ins
        className="adsbygoogle"
        style={{ display: "block", width: "100%", minHeight: "100px" }}
        data-ad-client={adsenseId}
        data-ad-slot="2020882637" // Ad slot padrão para feed
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}

// Impede SSR para garantir compatibilidade com a injeção via DOM do Google
const FeedAd = dynamic(() => Promise.resolve(AdSenseInner), { ssr: false });

export default FeedAd;
