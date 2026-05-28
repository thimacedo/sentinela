'use client';

import { Shield, FileText, Lock, Eye, AlertTriangle } from 'lucide-react';

export default function TokenExplanation() {
  const operations = [
    {
      icon: <FileText className="w-5 h-5 text-brand-primary" />,
      title: 'Desbloqueio de Dossiê',
      cost: '350 CI',
      desc: 'Análise pericial completa de um alvo com exportação legal.'
    },
    {
      icon: <Eye className="w-5 h-5 text-purple-500" />,
      title: 'Ativar Deep Scrape',
      cost: '150 CI',
      desc: 'Rastreio em profundidade de redes coordenadas (Diário).'
    },
    {
      icon: <Shield className="w-5 h-5 text-emerald-500" />,
      title: 'Adição de Novo Alvo',
      cost: '500 CI',
      desc: 'Inclusão de um novo político no pipeline de monitoramento.'
    },
    {
      icon: <AlertTriangle className="w-5 h-5 text-orange-500" />,
      title: 'Auditoria Forense (Solenya)',
      cost: '850 CI',
      desc: 'Investigação automatizada avançada sobre ataque coordenado.'
    }
  ];

  return (
    <div className="bg-bg-main border border-border-main rounded-2xl p-8 mb-12 shadow-inner">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 bg-brand-primary/10 rounded-xl flex items-center justify-center">
          <Lock className="w-6 h-6 text-brand-primary" />
        </div>
        <div>
          <h2 className="text-2xl font-black text-text-main tracking-tight">Custo Operacional de Inteligência</h2>
          <p className="text-sm text-text-muted font-mono mt-1">
            Operações na rede Sentinela consomem Créditos de Inteligência (CI) devido ao uso massivo de processamento neural e proxies residenciais.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {operations.map((op, idx) => (
          <div key={idx} className="bg-bg-card border border-border-main rounded-xl p-5 hover:border-brand-primary/40 transition-all">
            <div className="flex items-start justify-between mb-4">
              <div className="w-10 h-10 bg-bg-main rounded-lg flex items-center justify-center border border-border-main">
                {op.icon}
              </div>
              <span className="px-2.5 py-1 bg-brand-primary/10 text-brand-primary text-xs font-black font-mono rounded border border-brand-primary/20">
                {op.cost}
              </span>
            </div>
            <h3 className="text-sm font-bold text-text-main mb-2">{op.title}</h3>
            <p className="text-xs text-text-muted leading-relaxed">{op.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
