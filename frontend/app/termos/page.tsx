'use client';

import Link from 'next/link';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export default function TermosPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-10">
      {/* Header */}
      <div className="border-b border-border-main pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-text-main uppercase">
          Termos de Uso
        </h1>
        <p className="text-sm text-text-muted mt-2 font-mono">
          Última atualização: 27 de maio de 2026
        </p>
      </div>

      {/* Content */}
      <div className="space-y-6 text-sm text-text-muted leading-relaxed">
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">1. Natureza do Observatório</h2>
          <p>
            O Sentinela Democrática é uma plataforma autônoma de interesse público dedicada ao monitoramento e análise de tendências de discurso em redes sociais de agentes públicos, candidatos e pessoas politicamente expostas. Nossos serviços visam fornecer transparência de dados e subsidiar o debate democrático.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">2. Fonte e Limitação dos Dados</h2>
          <p>
            Todas as informações exibidas neste observatório são coletadas de postagens públicas em redes sociais. O processamento dessas informações utiliza inteligência artificial com base no protocolo de classificação MCA v2.2.
          </p>
          <p className="bg-bg-card border border-border-main p-4 rounded-lg text-xs italic">
            <strong>Nota de Isenção:</strong> A classificação automatizada de postagens pode gerar falsos positivos ou falsos negativos. Os dados apresentados servem como indício analítico técnico e de pesquisa, não constituindo juízo definitivo ou acusação de qualquer natureza jurídica.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">3. Propriedade Intelectual e Uso Aceitável</h2>
          <p>
            O uso dos dados agregados e análises geradas pelo observatório é livre para fins de pesquisa acadêmica, jornalismo e auditoria pública, desde que citada a fonte (Sentinela). É vedado o uso de técnicas de extração de dados automatizada (scraping) que sobrecarreguem ou prejudiquem a estabilidade técnica de nossa plataforma.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">4. Alterações nos Termos</h2>
          <p>
            Reservamo-nos o direito de atualizar este documento periodicamente para refletir mudanças metodológicas, técnicas ou legais. O uso continuado da plataforma implica na aceitação das diretrizes atualizadas.
          </p>
        </section>
      </div>

      <AdSenseSlot adSlot="2020882637" format="horizontal" />

      {/* Footer Navigation */}
      <div className="pt-8 border-t border-border-main flex gap-4">
        <Link href="/" className="text-xs font-mono font-bold text-brand-primary hover:underline">
          ← Voltar ao Início
        </Link>
      </div>
    </div>
  );
}
