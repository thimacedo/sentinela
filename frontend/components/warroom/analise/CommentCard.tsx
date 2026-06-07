import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Calendar, Info } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface Comment {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  confianca_ia: number;
  is_hate: boolean;
  data_coleta: string;
  username_alvo: string;
  analise_pericial?: string;
  ccf_sync?: number;
}

interface CommentCardProps {
  c: Comment;
}

export default function CommentCard({ c }: CommentCardProps) {
  const getRiskColor = (category: string, isHate: boolean, confidence: number) => {
    if (category === 'ERRO') return 'text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-900 bg-purple-50 dark:bg-purple-900/10';
    if (!isHate) return 'text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-900/10';
    if (confidence > 0.8) return 'text-red-600 dark:text-red-400 border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/10';
    if (confidence > 0.5) return 'text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-900 bg-orange-50 dark:bg-orange-900/10';
    return 'text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900 bg-yellow-50 dark:bg-yellow-900/10';
  };

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl p-6 shadow-sm hover:border-brand-primary/20 transition-all duration-200">
      {/* Cabeçalho do Post */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center font-black text-brand-primary text-sm">
            {c.username_alvo.substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-black text-text-main text-sm">@{c.username_alvo}</span>
              <span className="text-[10px] text-text-muted font-medium">• alvo monitorado</span>
            </div>
            <div className="flex items-center gap-1 text-[10px] text-text-muted font-mono mt-0.5">
              <Calendar className="w-3 h-3" />
              {new Date(c.data_coleta).toLocaleString('pt-BR')}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <Badge className={`px-2.5 py-0.5 text-[9px] font-black uppercase rounded-sm border ${getRiskColor(c.categoria_ia, c.is_hate, c.confianca_ia)}`}>
            {c.categoria_ia}
          </Badge>
          {c.ccf_sync && c.ccf_sync > 0.4 && (
            <span className="text-[8px] font-black text-brand-primary bg-brand-primary/5 px-1.5 py-0.5 rounded border border-brand-primary/10 animate-pulse">
              Coordenação: {(c.ccf_sync * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      {/* Conteúdo Central do Comentário */}
      <div className="mt-4 p-5 bg-bg-main/50 border border-border-main rounded-xl overflow-x-auto">
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {c.texto_bruto}
          </ReactMarkdown>
        </div>
      </div>

      {/* Detalhes Técnicos (Se houver perícia) */}
      {c.analise_pericial && (
        <div className="mt-3 flex items-start gap-2 p-3 bg-brand-primary/5 rounded-lg border border-brand-primary/10">
          <Info className="w-3.5 h-3.5 text-brand-primary shrink-0 mt-0.5" />
          <div className="text-[10px] text-text-muted italic leading-relaxed">
            <span className="font-bold text-brand-primary not-italic uppercase tracking-tighter mr-1">Parecer Técnico:</span>
            {c.analise_pericial}
          </div>
        </div>
      )}

      {/* Rodapé do Card */}
      <div className="mt-4 flex items-center justify-between gap-4 border-t border-border-main/50 pt-4">
        <div className="flex items-center gap-2 w-full max-w-xs">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Confiança:</span>
          <div className="text-xs font-black text-text-main w-12 text-right">
            {(c.confianca_ia * 100).toFixed(1)}%
          </div>
          <div className="flex-1 h-1.5 bg-bg-main rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-1000 ${c.is_hate ? 'bg-brand-primary' : 'bg-emerald-500'}`} 
              style={{ width: `${c.confianca_ia * 100}%` }}
            />
          </div>
        </div>
        <div className="text-[9px] font-mono text-text-muted opacity-50 uppercase">
          ID: {c.id.substring(0, 8)}
        </div>
      </div>
    </div>
  );
}
