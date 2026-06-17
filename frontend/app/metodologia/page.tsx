'use client';

import Link from 'next/link';
import { BookOpen, ShieldCheck, Cpu, Database } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import { JsonLd } from '@/components/JsonLd';

const breadcrumbSchema = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://sentinelademocratica.com.br"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Metodologia Científica",
      "item": "https://sentinelademocratica.com.br/metodologia"
    }
  ]
};

const webPageSchema = {
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Metodologia Científica do Observatório",
  "description": "Protocolo Analítico MCA v2.2 (Multi-Channel Assessment) utilizado pelo Sentinela Democrática para monitoramento de ódio em plataformas sociais.",
  "url": "https://sentinelademocratica.com.br/metodologia",
  "publisher": {
    "@type": "Organization",
    "name": "Sentinela Democrática",
    "url": "https://sentinelademocratica.com.br"
  }
};

export default function MetodologiaPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-10">
      <JsonLd data={breadcrumbSchema} />
      <JsonLd data={webPageSchema} />
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-brand-primary" />
            Metodologia Científica
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Protocolo Analítico MCA v2.2 (Multi-Channel Assessment)
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-8 text-sm text-text-muted leading-relaxed">
        {/* Intro */}
        <p className="text-base text-text-main">
          O Observatório utiliza uma abordagem metodológica baseada em coleta automatizada multicamadas (Multi-tier) e inteligência artificial para avaliar e categorizar a integridade do debate político nas plataformas sociais.
        </p>

        {/* Grid de Metodologia */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
          <div className="bg-bg-card border border-border-main p-6 rounded-xl space-y-3">
            <h3 className="text-base font-bold text-text-main flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-500" /> 1. Camada de Coleta (Tiers)
            </h3>
            <p className="text-xs">
              A captura de postagens públicas opera sob um sistema de redundância dinâmico:
            </p>
            <ul className="text-xs list-disc pl-4 space-y-1">
              <li><strong>Tier 1:</strong> Acesso direto via chamadas GraphQL estruturadas (baixa latência).</li>
              <li><strong>Tier 2:</strong> Automação Playwright com técnicas stealth de carregamento de DOM.</li>
              <li><strong>Tier 3:</strong> Crawling e processamento distribuído via rede Zyte (Resiliência secundária).</li>
            </ul>
          </div>

          <div className="bg-bg-card border border-border-main p-6 rounded-xl space-y-3">
            <h3 className="text-base font-bold text-text-main flex items-center gap-2">
              <Cpu className="w-5 h-5 text-emerald-500" /> 2. Classificação Semântica (MCA v2.2)
            </h3>
            <p className="text-xs">
              Os textos coletados passam por filtragem de lixo lexical (MSAL) e, em seguida, por auditoria de IA local (Llama/Mistral) e IA em nuvem (Gemini) baseada em quatro categorias de relevância:
            </p>
            <ul className="text-xs list-disc pl-4 space-y-1">
              <li><strong>Insulto Ad Hominem:</strong> Ataques de cunho puramente pessoal voltados à desqualificação.</li>
              <li><strong>Ataque Institucional:</strong> Linguagem de hostilidade direcionada à integridade do processo eleitoral ou de órgãos de Estado.</li>
              <li><strong>Discurso de Ódio:</strong> Manifestações que promovem violência ou discriminação estrutural.</li>
              <li><strong>Neutro:</strong> Crítica política legítima ou postagem factual/informativa.</li>
            </ul>
          </div>
        </div>

        {/* Índice de Resiliência */}
        <section className="space-y-3 pt-4">
          <h2 className="text-lg font-bold text-text-main flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-500" /> O Índice de Resiliência Democrática (IRD)
          </h2>
          <p>
            O Índice de Resiliência Democrática (IRD) é a nossa métrica principal para mensurar a saúde do debate político. Calculado de forma diária, ele pondera a proporção de conteúdos classificados como saudáveis (crítica cívica padrão, fatos ou neutros) em relação ao volume total de dados processados.
          </p>
          <div className="bg-bg-card border-l-4 border-brand-primary/40 p-4 rounded-r-lg text-xs font-mono">
            IRD = (Total de Posts - (Insultos + Ataques + Ódio)) / Total de Posts * 100
          </div>
          <p>
            Valores de IRD acima de 90% indicam um ecossistema com altos padrões de debate cívico e incidência controlada de ataques coordenados.
          </p>
        </section>

        {/* Integridade Científica */}
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">3. Transparência e Auditoria</h2>
          <p>
            Garantindo a rastreabilidade metodológica, o Sentinela mantém registros anonimizados do prompt de classificação e das chaves de decisão. Todos os dados históricos podem ser analisados sob demanda no módulo de Relatórios e Dossiês.
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
