'use client';

import Link from 'next/link';

export default function LgpdPage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-10">
      {/* Header */}
      <div className="border-b border-border-main pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-text-main uppercase">
          LGPD e Proteção de Dados
        </h1>
        <p className="text-sm text-text-muted mt-2 font-mono">
          Tratamento de dados pessoais de interesse público em conformidade com a Lei nº 13.709/2018
        </p>
      </div>

      {/* Content */}
      <div className="space-y-6 text-sm text-text-muted leading-relaxed">
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">1. Base Legal para o Tratamento de Dados</h2>
          <p>
            O tratamento de dados pessoais no âmbito do Sentinela é fundamentado no Artigo 7º, incisos IX (legítimo interesse do controlador) e III (administração pública e interesse público/transparência) da Lei Geral de Proteção de Dados (LGPD).
          </p>
          <p>
            Por monitorarmos perfis e manifestações públicas de agentes políticos, detentores de cargos eletivos e candidatos a cargos públicos, a coleta é restrita a <strong>dados manifestamente públicos</strong> divulgados voluntariamente pelos próprios titulares (conforme Art. 7º, § 4º da LGPD).
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">2. Finalidade do Tratamento</h2>
          <p>
            Os dados coletados destinam-se exclusivamente ao fomento da transparência democrática, realização de análises volumétricas estatísticas e identificação de padrões de conduta nocivos no debate político online. Não há fins lucrativos ou comerciais no tratamento dessas informações.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">3. Minimização e Segurança da Informação</h2>
          <p>
            Adotamos medidas rígidas de segurança técnica e organizacional para evitar o processamento de dados excessivos, sensíveis ou de menores de idade. Apenas o conteúdo textual público das postagens e dados de identificação pública do perfil (username, biografia e partido) são mantidos em nosso banco de dados blindado com RLS (Row Level Security).
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">4. Direitos dos Titulares</h2>
          <p>
            Mesmo tratando-se de dados públicos de interesse público, os titulares podem exercer seus direitos de confirmação, acesso ou solicitar a retificação de classificações técnicas diretamente pelo nosso canal de suporte ou encarregado de proteção de dados.
          </p>
          <p className="bg-bg-card border border-border-main p-4 rounded-lg text-xs">
            <strong>Contato do DPO / Encarregado:</strong> lgpd@sentinela.democratica
          </p>
        </section>
      </div>

      {/* Footer Navigation */}
      <div className="pt-8 border-t border-border-main flex gap-4">
        <Link href="/" className="text-xs font-mono font-bold text-brand-primary hover:underline">
          ← Voltar ao Início
        </Link>
      </div>
    </div>
  );
}
