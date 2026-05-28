import PricingGrid from '@/components/pricing/PricingGrid';
import TokenExplanation from '@/components/pricing/TokenExplanation';
import Link from 'next/link';
import { ArrowLeft, ShieldAlert } from 'lucide-react';

export const metadata = {
  title: 'Protocolos de Acesso - Sentinela Democrática',
};

export default function PlanosPage() {
  return (
    <div className="min-h-screen bg-bg-main">
      {/* Navbar simplificada */}
      <nav className="border-b border-border-main bg-bg-card">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-text-muted hover:text-brand-primary transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-widest">Retornar ao Radar</span>
          </Link>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-brand-primary/10 border border-brand-primary/20 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
            <span className="text-[10px] font-black text-brand-primary uppercase tracking-widest">Rede Segura</span>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-16">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded-full mb-6 text-[10px] font-black uppercase tracking-widest">
            <ShieldAlert className="w-3.5 h-3.5" />
            Acesso Restrito
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-text-main tracking-tighter mb-4">
            Expanda seu Raio de Cobertura Analítica.
          </h1>
          <p className="text-lg text-text-muted max-w-2xl mx-auto leading-relaxed">
            As operações de monitoramento profundo e criação de dossiês requerem alto processamento distribuído. Adquira Créditos de Inteligência (CI) para financiar suas operações na rede Sentinela.
          </p>
        </div>

        <TokenExplanation />
        <PricingGrid />

        <div className="mt-20 text-center space-y-4">
          <h3 className="text-lg font-bold text-text-main">Por que não utilizamos Real (R$) diretamente nas análises?</h3>
          <p className="text-sm text-text-muted max-w-3xl mx-auto leading-relaxed">
            A arquitetura Sentinela opera através de nós distribuídos (proxies residenciais e APIs de linguagem neutra). 
            O custo de extração varia conforme as defesas da rede social do alvo. A utilização de Créditos de Inteligência (CI) 
            garante estabilidade contábil independentemente das flutuações de custo da infraestrutura subjacente de IA.
          </p>
        </div>
      </main>
    </div>
  );
}
