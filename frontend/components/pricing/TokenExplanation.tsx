'use client';

import { Shield, FileText, Lock, Eye, AlertTriangle } from 'lucide-react';

export default function TokenExplanation() {
  const operations = [
    {
      icon: <FileText className="w-5 h-5 text-brand-primary" />,
      title: 'Dossiê Forense Completo',
      cost: '350 CI',
      desc: 'Antecipe crises. Obtenha relatórios técnicos irrefutáveis com o histórico estruturado de evidências do alvo.'
    },
    {
      icon: <Eye className="w-5 h-5 text-purple-500" />,
      title: 'Radar de Narrativas Inimigas',
      cost: '150 CI',
      desc: 'Visão além do óbvio. Mapeie campanhas de desinformação antes que elas atinjam o domínio público.'
    },
    {
      icon: <Shield className="w-5 h-5 text-emerald-500" />,
      title: 'Inclusão de Alvo Estratégico',
      cost: '500 CI',
      desc: 'Expanda sua malha de inteligência. Insira novos adversários ou aliados no pipeline de monitoramento PASA 24/7.'
    },
    {
      icon: <AlertTriangle className="w-5 h-5 text-orange-500" />,
      title: 'Feed de Alertas em Tempo Real',
      cost: '850 CI',
      desc: 'A vantagem da reação imediata. Acesso contínuo e prioritário às detecções críticas filtradas por Inteligência Artificial.'
    }
  ];

  return (
    <div className="bg-bg-main border border-border-main rounded-2xl p-8 mb-12 shadow-inner">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 bg-brand-primary/10 rounded-xl flex items-center justify-center">
          <Lock className="w-6 h-6 text-brand-primary" />
        </div>
        <div>
          <h2 className="text-2xl font-black text-text-main tracking-tight">Investimento Tático de Inteligência</h2>
          <p className="text-sm text-text-muted font-mono mt-1">
            Cada aporte de <strong className="text-brand-primary">Créditos de Inteligência (CI)</strong> converte o uso massivo da nossa malha neural e proxies residenciais em <strong>vantagem assimétrica e poder antecipado de decisão</strong>.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {operations.map((op, idx) => (
          <div key={idx} className="bg-bg-card border border-border-main rounded-xl p-5 hover:border-brand-primary/40 transition-all flex flex-col h-full group relative overflow-hidden">
            {/* Efeito Hover Glow */}
            <div className="absolute inset-0 bg-gradient-to-tr from-brand-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
            
            <div className="flex items-start justify-between mb-4 z-10">
              <div className="w-10 h-10 bg-bg-main rounded-lg flex items-center justify-center border border-border-main group-hover:border-brand-primary/30 transition-colors">
                {op.icon}
              </div>
              <span className="px-2.5 py-1 bg-brand-primary/10 text-brand-primary text-[10px] font-black font-mono rounded uppercase tracking-widest border border-brand-primary/20 shadow-[0_0_10px_rgba(var(--brand-primary),0.2)]">
                Aporte: {op.cost}
              </span>
            </div>
            <h3 className="text-sm font-bold text-text-main mb-2 z-10">{op.title}</h3>
            <p className="text-xs text-text-muted leading-relaxed z-10 flex-1">{op.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
