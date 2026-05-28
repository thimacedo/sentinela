'use client';

import Link from 'next/link';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export default function PrivacidadePage() {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4 space-y-10">
      {/* Header */}
      <div className="border-b border-border-main pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-text-main uppercase">
          Política de Privacidade
        </h1>
        <p className="text-sm text-text-muted mt-2 font-mono">
          Compromisso com a transparência e sigilo das informações do usuário
        </p>
      </div>

      {/* Content */}
      <div className="space-y-6 text-sm text-text-muted leading-relaxed">
        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">1. Visão Geral</h2>
          <p>
            O Sentinela Democrática tem como prioridade máxima a proteção e o respeito à privacidade dos visitantes do nosso site. Esta Política detalha como tratamos os dados decorrentes da sua navegação técnica no nosso observatório.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">2. Coleta de Dados de Navegação (Cookies e Logs)</h2>
          <p>
            Coletamos apenas dados técnicos estritamente necessários para o funcionamento e otimização do site:
          </p>
          <ul className="list-disc pl-4 space-y-1">
            <li>Endereço IP (mascarado ou anonimizado para fins de telemetria básica).</li>
            <li>Tipo de navegador, sistema operacional e páginas acessadas (para otimização de interface).</li>
            <li>Cookies de sessão que armazenam a preferência de tema (Claro/Escuro).</li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">3. Serviços de Terceiros e Anúncios</h2>
          <p>
            Esta plataforma utiliza o serviço de publicidade programática Google AdSense. O Google e parceiros terceiros usam cookies para veicular anúncios com base em visitas anteriores dos usuários a este ou a outros sites na internet. Os usuários podem optar por desativar a publicidade personalizada visitando as Configurações de anúncios do Google.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">4. Retenção de Dados e Descarte</h2>
          <p>
            Os dados de navegação técnica são mantidos por períodos curtos (máximo de 90 dias) nos logs de servidor para análise de performance e segurança cívica do site, sendo eliminados automaticamente após esse prazo.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-bold text-text-main">5. Contato</h2>
          <p>
            Se houver dúvidas ou solicitações em relação a esta Política de Privacidade, você poderá entrar em contato pelo e-mail: dpo@sentinela.democratica.
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
