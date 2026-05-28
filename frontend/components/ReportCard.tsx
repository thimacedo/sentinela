import React from 'react';
import { Report } from '@/app/relatorios/page';
import { Lock, FileText, Zap } from 'lucide-react';

interface ReportCardProps {
  report: Report;
  onBuy: (reportName: string) => void;
}

export default function ReportCard({ report, onBuy }: ReportCardProps) {
  const handleClick = () => {
    // Inicia fluxo gamificado de dedução de CI
    const confirm = window.confirm("Isso consumirá 350 CI do seu saldo. Deseja prosseguir com a descriptografia do Dossiê?");
    if (confirm) {
      onBuy(report.name);
    }
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl p-6 flex flex-col items-start transition-all hover:border-brand-primary/40 shadow-sm relative group overflow-hidden">
      <div className="absolute top-0 right-0 w-24 h-24 bg-brand-primary/5 rounded-full blur-2xl group-hover:bg-brand-primary/10 transition-colors pointer-events-none" />
      
      <div className="flex items-start justify-between w-full mb-4">
        <div className="w-12 h-12 rounded-xl bg-bg-main border border-border-main flex items-center justify-center shadow-inner">
          <FileText className="w-6 h-6 text-brand-primary" />
        </div>
        <div className="px-2.5 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5">
          <Lock className="w-3 h-3" />
          Criptografado
        </div>
      </div>

      <h2 className="text-xl font-black text-text-main tracking-tight mb-2 leading-tight">{report.name.replace('.md', '').toUpperCase()}</h2>
      <p className="text-xs text-text-muted mb-6 font-mono uppercase tracking-widest opacity-70">Grau de Sigilo: Máximo</p>
      
      <div className="mt-auto w-full pt-6 border-t border-border-main">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] text-text-muted font-bold uppercase tracking-widest">Custo de Extração</span>
          <div className="flex items-end gap-1.5">
            <span className="text-2xl font-black text-text-main font-mono leading-none">350</span>
            <span className="text-xs font-bold text-brand-primary mb-0.5">CI</span>
          </div>
        </div>
        
        <button
          onClick={handleClick}
          className="w-full py-3 bg-brand-primary text-white rounded-xl text-xs font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-brand-primary/90 transition-all shadow-lg shadow-brand-primary/20"
        >
          <Zap className="w-4 h-4 fill-white" />
          Desbloquear Dossiê
        </button>
      </div>
    </div>
  );
}
