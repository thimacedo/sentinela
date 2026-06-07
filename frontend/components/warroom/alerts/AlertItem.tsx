import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Calendar, ShieldCheck } from 'lucide-react';
import { Comment } from '@/hooks/useInfiniteFeed';

interface AlertItemProps {
  alert: Comment;
  unlocked: boolean;
  onInvestigate: (alert: Comment) => void;
}

export default function AlertItem({ alert, unlocked, onInvestigate }: AlertItemProps) {
  const a = alert;
  
  return (
    <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm hover:border-red-500/20 transition-all duration-200">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center font-black text-red-600 text-sm">
            {a.candidatos?.username?.substring(0, 2).toUpperCase() || '??'}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-text-main text-sm">@{a.candidatos?.username || 'desconhecido'}</span>
              <span className="text-[10px] text-text-muted font-medium">• alvo afetado</span>
            </div>
            <div className="flex items-center gap-1 text-[10px] text-text-muted font-mono mt-0.5">
              <Calendar className="w-3 h-3" />
              {new Date(a.data_coleta).toLocaleString('pt-BR')}
            </div>
          </div>
        </div>
        <Badge className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 text-[8px] font-black uppercase rounded-sm h-4">
          {a.categoria_ia}
        </Badge>
      </div>

      <div className="mt-4 p-4 bg-bg-main/50 border border-border-main rounded-xl">
        <p className="text-sm text-text-main leading-relaxed italic">
          "{unlocked ? a.texto_bruto : "Conteúdo defasado (Acesso Premium Necessário)"}"
        </p>
      </div>

      <div className="mt-4 flex items-center justify-between gap-4 border-t border-border-main/50 pt-4">
        <button 
          onClick={() => onInvestigate(alert)}
          className="flex items-center gap-2 px-3 py-1.5 bg-bg-card hover:bg-bg-main border border-border-main text-[10px] font-black uppercase text-red-600 dark:text-red-400 rounded-lg transition-all shadow-sm"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          Investigar
        </button>
      </div>
    </div>
  );
}
