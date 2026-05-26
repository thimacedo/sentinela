'use client';

import { BookOpen, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

export default function MethodologyBox() {
  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 border-b border-slate-700 pb-4">
        <BookOpen className="w-6 h-6 text-blue-400" />
        <h3 className="text-lg font-bold text-white">📖 Sobre Este Observatório</h3>
      </div>

      {/* Description */}
      <div className="space-y-4 mb-6">
        <div>
          <p className="text-sm text-slate-300 mb-3">
            <strong>Sentinela</strong> monitora padrões de discurso em redes sociais para promover transparência e alimentar o debate democrático. Aqui você encontra análises sobre ódio, violência e desinformação em posts de candidatos e políticos.
          </p>
        </div>

        {/* What We Do */}
        <div>
          <h4 className="text-sm font-bold text-emerald-400 mb-2 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            O Que Fazemos
          </h4>
          <ul className="space-y-1 ml-6">
            <li className="text-xs text-slate-400">✓ Coleta e análise de posts públicos em redes sociais</li>
            <li className="text-xs text-slate-400">✓ Identificação de padrões de discurso de ódio e violência</li>
            <li className="text-xs text-slate-400">✓ Relatórios forenses com classificação semântica</li>
            <li className="text-xs text-slate-400">✓ Alertas contextualizados sobre picos anormais</li>
          </ul>
        </div>

        {/* Limitations */}
        <div>
          <h4 className="text-sm font-bold text-yellow-400 mb-2 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Limitações Importantes
          </h4>
          <ul className="space-y-1 ml-6">
            <li className="text-xs text-slate-400">
              ⚠️ Não substitui análise humana — use como ferramenta de pesquisa
            </li>
            <li className="text-xs text-slate-400">
              ⚠️ Baseado em posts públicos — não detecta contas privadas
            </li>
            <li className="text-xs text-slate-400">
              ⚠️ Classificação por IA — sujeita a falsos positivos/negativos
            </li>
            <li className="text-xs text-slate-400">
              ⚠️ Não visa julgar políticos, apenas informar a população
            </li>
          </ul>
        </div>

        {/* Methodology */}
        <div>
          <h4 className="text-sm font-bold text-blue-400 mb-2 flex items-center gap-2">
            <HelpCircle className="w-4 h-4" />
            Metodologia
          </h4>
          <div className="ml-6 space-y-2">
            <p className="text-xs text-slate-400">
              <strong>Coleta:</strong> APIs de redes sociais (Instagram, Twitter, etc.)
            </p>
            <p className="text-xs text-slate-400">
              <strong>Processamento:</strong> Limpeza, tokenização e análise semântica com Qwen 2.5
            </p>
            <p className="text-xs text-slate-400">
              <strong>Classificação:</strong> Protocolo PASA v50 — critérios rigorosos de ódio e violência
            </p>
            <p className="text-xs text-slate-400">
              <strong>Atualização:</strong> Tempo real a cada 6 horas (processamento em batch)
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded p-3 text-xs text-blue-300">
        <p>
          📚 Para mais detalhes, consulte nossa{' '}
          <button className="underline hover:text-blue-200">documentação técnica</button> ou{' '}
          <button className="underline hover:text-blue-200">publicações</button>.
        </p>
      </div>
    </div>
  );
}
