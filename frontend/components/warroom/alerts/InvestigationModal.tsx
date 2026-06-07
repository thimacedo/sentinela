import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { fetchApi } from '@/lib/api';
import { Comment } from '@/hooks/useInfiniteFeed';

interface InvestigationModalProps {
  investigatingAlert: Comment;
  onClose: () => void;
}

export default function InvestigationModal({ investigatingAlert, onClose }: InvestigationModalProps) {
  const queryClient = useQueryClient();
  const [analiseTexto, setAnaliseTexto] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const a = investigatingAlert;

  const handleDiscard = async () => {
    setIsSaving(true);
    try {
      await fetchApi('/api/v1/alerts/false-positive', { method: 'POST', body: JSON.stringify({ id: a.id }) });
      queryClient.invalidateQueries({ queryKey: ['active-alerts-list'] });
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await fetchApi('/api/v1/audit/validate', { 
        method: 'POST', 
        body: JSON.stringify({ comment_id: a.id, rotulo_correto: 'hate', analise_pericial: analiseTexto }) 
      });
      queryClient.invalidateQueries({ queryKey: ['active-alerts-list'] });
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-bg-card border border-border-main rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
          <div>
            <h3 className="text-lg font-black text-text-main tracking-tight uppercase">Análise Analítica de Indício</h3>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-main text-xs font-bold uppercase tracking-wider transition-colors">Fechar</button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Alvo</span>
            <div className="font-black text-red-600 dark:text-red-400 text-sm mt-1">@{a.candidatos?.username}</div>
          </div>
          
          <div>
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Conteúdo Analisado</span>
            <div className="p-3 bg-bg-main/50 border border-border-main rounded-lg text-xs text-text-main/90 italic mt-1">
              "{a.texto_bruto}"
            </div>
          </div>

          <div>
            <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Indícios e Análise de Linguagem</label>
            <textarea 
              rows={4}
              value={analiseTexto}
              onChange={(e) => setAnaliseTexto(e.target.value)}
              placeholder="Descreva aqui os indícios linguísticos..."
              className="w-full p-3 bg-bg-main/50 border border-border-main rounded-lg text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors leading-relaxed placeholder:text-text-muted"
            />
          </div>
        </div>

        <div className="p-4 bg-bg-main/30 border-t border-border-main flex justify-between gap-3">
          <button 
            onClick={handleDiscard}
            disabled={isSaving}
            className="px-3 py-2 border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 text-[10px] font-black uppercase text-red-600 dark:text-red-400 rounded-lg transition-all"
          >
            Descartar (Falso Positivo)
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-3 py-2 border border-border-main bg-bg-card hover:bg-bg-main text-[10px] font-bold uppercase text-text-muted hover:text-text-main rounded-lg transition-all">Cancelar</button>
            <button 
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-brand-primary hover:bg-brand-primary/90 text-[10px] font-black uppercase text-white rounded-lg transition-all shadow-md"
            >
              {isSaving ? 'Salvando...' : 'Salvar Análise'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
