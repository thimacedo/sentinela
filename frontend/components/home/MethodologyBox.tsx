'use client';

import { BookOpen, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

export default function MethodologyBox() {
  return (
    <div className="bg-bg-card border border-border-main rounded-xl p-8 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8 border-b border-border-main pb-4">
        <BookOpen className="w-6 h-6 text-brand-primary" />
        <h3 className="text-xl font-black text-text-main tracking-tight">📖 Sobre Este Observatório</h3>
      </div>

      {/* Description */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div className="space-y-6">
          <div>
            <p className="text-base text-text-main leading-relaxed">
              O <strong>Sentinela</strong> monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático brasileiro.
            </p>
            <p className="text-sm text-text-muted mt-3 leading-relaxed">
              Nossa plataforma identifica tendências de ódio, hostilidade e desinformação, fornecendo dados técnicos para a sociedade civil e órgãos de controle.
            </p>
          </div>

          {/* What We Do */}
          <div>
            <h4 className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mb-3 flex items-center gap-2 uppercase tracking-widest">
              <CheckCircle2 className="w-4 h-4" />
              O Que Fazemos
            </h4>
            <ul className="space-y-2 ml-1">
              {[
                'Coleta autônoma de posts públicos em redes sociais',
                'Identificação de padrões de discurso de ódio e violência',
                'Relatórios analíticos com classificação semântica MCA v2.2',
                'Alertas em tempo real sobre picos anormais de hostilidade'
              ].map((item, i) => (
                <li key={i} className="text-xs text-text-muted flex items-start gap-2">
                  <span className="text-emerald-500 mt-0.5">✓</span> {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="space-y-6">
          {/* Limitations */}
          <div>
            <h4 className="text-sm font-bold text-amber-600 dark:text-amber-500 mb-3 flex items-center gap-2 uppercase tracking-widest">
              <AlertCircle className="w-4 h-4" />
              Limitações Importantes
            </h4>
            <ul className="space-y-2 ml-1">
              {[
                'Não substitui análise humana — ferramenta de pesquisa',
                'Baseado em posts públicos — não detecta contas privadas',
                'Classificação por IA — sujeita a falsos positivos',
                'Não visa julgamento político, apenas transparência de dados'
              ].map((item, i) => (
                <li key={i} className="text-xs text-text-muted flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">⚠️</span> {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Methodology */}
          <div className="bg-bg-main border border-border-main rounded-xl p-5">
            <h4 className="text-xs font-bold text-brand-primary mb-4 flex items-center gap-2 uppercase tracking-tighter">
              <HelpCircle className="w-4 h-4" />
              Metodologia Técnica
            </h4>
            <div className="space-y-3">
              {[
                { label: 'Coleta', val: 'Motores Playwright v2 / Zyte' },
                { label: 'Processamento', val: 'Análise semântica Híbrida (Mistral/Ollama)' },
                { label: 'Protocolo', val: 'PASA v70.4 — Critérios de Análise' },
                { label: 'Frequência', val: 'Ciclos de 24h com Autopilot L3' }
              ].map((item, i) => (
                <p key={i} className="text-[10px] text-text-muted leading-tight">
                  <strong className="text-text-main uppercase mr-1">{item.label}:</strong> {item.val}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-brand-primary/5 border border-brand-primary/10 rounded-xl p-4 text-xs text-brand-primary flex justify-between items-center flex-wrap gap-4">
        <p className="font-medium">
          📚 Explore nossa documentação técnica para entender os algoritmos.
        </p>
        <div className="flex gap-4">
          <button className="underline font-bold hover:text-blue-600 transition-colors">Documentação</button>
          <button className="underline font-bold hover:text-blue-600 transition-colors">Publicações</button>
        </div>
      </div>
    </div>
  );
}
