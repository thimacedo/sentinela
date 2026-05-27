'use client';
import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ShieldAlert, Zap } from 'lucide-react';
import { fetchApi } from '@/lib/api';
import { supabase } from '@/lib/supabase';

interface Alert {
  id: string;
  texto_bruto: string;
  categoria_ia: string;
  data_coleta: string;
  candidatos: { username: string };
  confianca_ia: number;
  analise_pericial?: string;
}

export default function AlertsTab() {
  const queryClient = useQueryClient();
  const [investigatingAlert, setInvestigatingAlert] = useState<Alert | null>(null);
  const [analiseTexto, setAnaliseTexto] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ['active-alerts-list'],
    queryFn: async () => {
      try {
        return await fetchApi('/api/v1/alerts/active');
      } catch (error) {
        console.warn("Erro ao buscar alertas da API, tentando fallback Supabase:", error);
      }

      // Fallback Supabase
      try {
        const { data: comments, error } = await supabase
          .from('comentarios')
          .select('id, texto_bruto, categoria_ia, data_coleta, candidato_id, confianca_ia, analise_pericial')
          .eq('is_hate', true)
          .order('data_coleta', { ascending: false })
          .limit(20);

        if (error || !comments) {
          console.error("Erro no fallback Supabase de alertas:", error);
          return [];
        }

        return comments.map((c: any) => ({
          id: c.id,
          texto_bruto: c.texto_bruto,
          categoria_ia: c.categoria_ia || 'OUTROS',
          data_coleta: c.data_coleta,
          candidatos: { username: c.candidato_id || 'desconhecido' },
          confianca_ia: c.confianca_ia,
          analise_pericial: c.analise_pericial
        }));
      } catch (err) {
        console.error("Erro crítico no fallback de alertas do Supabase:", err);
        return [];
      }
    },
    refetchInterval: 10000,
  });

  return (
    <div className="bg-bg-card border border-border-main rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
        <div>
          <h2 className="text-xl font-black text-text-main tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-500 animate-pulse" />
            Alertas de Segurança
          </h2>
          <p className="text-xs text-text-muted font-medium uppercase tracking-widest mt-1">Incidentes Críticos em Tempo Real</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full">
          <Zap className="w-3.5 h-3.5 text-red-500 fill-red-500" />
          <span className="text-[10px] font-bold text-red-600 dark:text-red-400 uppercase">Live Monitor</span>
        </div>
      </div>

      <Table>
        <TableHeader className="bg-bg-main/30">
          <TableRow className="border-border-main hover:bg-transparent">
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Alvo</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider px-6">Conteúdo Hostil</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-center">Captura</TableHead>
            <TableHead className="text-text-muted font-bold uppercase text-[10px] tracking-wider text-right px-6">Ação</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted animate-pulse font-mono text-xs">
                INTERCEPTANDO FREQUÊNCIAS DE ÓDIO...
              </TableCell>
            </TableRow>
          ) : alerts.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-20 text-text-muted font-mono text-xs">
                ESPECTRO LIMPO. NENHUM INCIDENTE ATIVO.
              </TableCell>
            </TableRow>
          ) : (
            alerts.map((a) => (
              <TableRow key={a.id} className="border-border-main hover:bg-red-500/5 transition-colors">
                <TableCell className="px-6 py-4">
                  <div className="font-black text-red-600 dark:text-red-400 text-sm">@{a.candidatos?.username}</div>
                </TableCell>
                <TableCell className="max-w-md px-6 py-4">
                  <div className="flex flex-col gap-2">
                    <p className="text-sm text-text-main leading-relaxed">"{a.texto_bruto}"</p>
                    <Badge className="w-fit bg-red-600 dark:bg-red-500 text-white border-none text-[8px] font-black uppercase rounded-sm h-4">
                      {a.categoria_ia}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell className="text-center py-4 text-[10px] font-mono text-text-muted">
                  {new Date(a.data_coleta).toLocaleString('pt-BR')}
                </TableCell>
                <TableCell className="text-right px-6 py-4">
                  <button 
                    onClick={() => {
                      setInvestigatingAlert(a);
                      setAnaliseTexto(a.analise_pericial || '');
                    }}
                    className="px-3 py-1.5 bg-bg-card hover:bg-bg-main border border-border-main text-[10px] font-black uppercase text-red-600 dark:text-red-400 rounded-lg transition-all shadow-sm"
                  >
                    Investigar
                  </button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      
      <div className="p-4 bg-red-500/5 border-t border-border-main text-center text-[10px] font-bold text-red-600 dark:text-red-400 uppercase tracking-widest">
        Atenção: Os dados acima são processados por IA e requerem validação técnica.
      </div>

      {/* Modal de Investigação / Análise Analítica */}
      {investigatingAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-bg-card border border-border-main rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
            {/* Header */}
            <div className="p-6 border-b border-border-main flex justify-between items-center bg-bg-main/50">
              <div>
                <h3 className="text-lg font-black text-text-main tracking-tight uppercase">Análise Analítica de Indício</h3>
                <p className="text-[10px] text-text-muted font-bold uppercase tracking-widest mt-1">Status: Investigação de Discurso</p>
              </div>
              <button 
                onClick={() => setInvestigatingAlert(null)}
                className="text-text-muted hover:text-text-main text-xs font-bold uppercase tracking-wider transition-colors"
              >
                Fechar
              </button>
            </div>
            
            {/* Body */}
            <div className="p-6 space-y-4">
              <div>
                <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Alvo Identificado</span>
                <div className="font-black text-red-600 dark:text-red-400 text-sm mt-1">@{investigatingAlert.candidatos?.username || 'desconhecido'}</div>
              </div>
              
              <div>
                <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Conteúdo Analisado</span>
                <div className="p-3 bg-bg-main/50 border border-border-main rounded-lg text-xs text-text-main/90 italic leading-relaxed mt-1">
                  "{investigatingAlert.texto_bruto}"
                </div>
              </div>

              <div>
                <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Classificação Automática</span>
                <div className="flex gap-4 items-center mt-1.5">
                  <Badge className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 text-[9px] font-black uppercase rounded-sm h-5">
                    {investigatingAlert.categoria_ia}
                  </Badge>
                  <span className="text-[11px] font-bold text-text-muted">
                    Confiança: {((investigatingAlert.confianca_ia || 0.95) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-[9px] font-bold text-text-muted uppercase tracking-wider mb-1.5">
                  Indícios e Análise de Linguagem
                </label>
                <textarea 
                  rows={4}
                  value={analiseTexto}
                  onChange={(e) => setAnaliseTexto(e.target.value)}
                  placeholder="Descreva aqui os indícios linguísticos, tom do discurso, potencial coordenado, etc. (Evite termos regulados como prova ou perícia)."
                  className="w-full p-3 bg-bg-main/50 border border-border-main rounded-lg text-xs text-text-main focus:outline-none focus:border-brand-primary transition-colors leading-relaxed placeholder:text-text-muted"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 bg-bg-main/30 border-t border-border-main flex justify-between gap-3">
              <button 
                onClick={async () => {
                  if (!investigatingAlert) return;
                  setIsSaving(true);
                  try {
                    await fetchApi('/api/v1/alerts/false-positive', {
                      method: 'POST',
                      body: JSON.stringify({ id: investigatingAlert.id }),
                    });
                    queryClient.invalidateQueries({ queryKey: ['active-alerts-list'] });
                    setInvestigatingAlert(null);
                  } catch (err) {
                    console.error(err);
                    alert("Erro ao descartar o incidente.");
                  } finally {
                    setIsSaving(false);
                  }
                }}
                disabled={isSaving}
                className="px-3 py-2 border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 text-[10px] font-black uppercase text-red-600 dark:text-red-400 rounded-lg transition-all"
              >
                Descartar (Falso Positivo)
              </button>
              <div className="flex gap-2">
                <button 
                  onClick={() => setInvestigatingAlert(null)}
                  className="px-3 py-2 border border-border-main bg-bg-card hover:bg-bg-main text-[10px] font-bold uppercase text-text-muted hover:text-text-main rounded-lg transition-all"
                >
                  Cancelar
                </button>
                <button 
                  onClick={async () => {
                    if (!investigatingAlert) return;
                    setIsSaving(true);
                    try {
                      await fetchApi('/api/v1/audit/validate', {
                        method: 'POST',
                        body: JSON.stringify({ 
                          comment_id: investigatingAlert.id,
                          rotulo_correto: 'hate',
                          analise_pericial: analiseTexto 
                        }),
                      });
                      queryClient.invalidateQueries({ queryKey: ['active-alerts-list'] });
                      setInvestigatingAlert(null);
                    } catch (err) {
                      console.error(err);
                      alert("Erro ao salvar análise analítica.");
                    } finally {
                      setIsSaving(false);
                    }
                  }}
                  disabled={isSaving}
                  className="px-4 py-2 bg-brand-primary hover:bg-brand-primary/90 disabled:opacity-50 text-[10px] font-black uppercase text-white rounded-lg transition-all shadow-md shadow-brand-primary/10"
                >
                  {isSaving ? 'Salvando...' : 'Salvar Análise'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
