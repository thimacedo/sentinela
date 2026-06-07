import React from 'react';
import { Badge } from '@/components/ui/badge';
import { useRouter } from 'next/navigation';

interface Target {
  id: string;
  username: string;
  nome_completo?: string;
  cargo?: string;
  partido?: string;
  estado?: string;
  status_monitoramento: string;
  tier: string;
  score_risco: number;
  nivel_risco: string;
  color: string;
  comentarios_odio_count: number;
  comentarios_totais_count?: number;
  breakdown?: Record<string, number>;
}

interface TargetCardProps {
  t: Target;
}

export default function TargetCard({ t }: TargetCardProps) {
  const router = useRouter();
  
  const totalHate = t.comentarios_odio_count || 0;
  const healthScore = Math.max(0, 100 - t.score_risco);

  return (
    <div 
      onClick={() => router.push(`/analise?target=${t.username}`)}
      className="group relative bg-bg-card border border-border-main rounded-3xl p-6 shadow-sm hover:shadow-2xl hover:border-brand-primary/40 hover:-translate-y-1 transition-all duration-500 cursor-pointer overflow-hidden"
    >
      {/* Background Glass Effect */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary/5 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-brand-primary/10 transition-colors duration-500" />
      
      <div className="flex items-start justify-between gap-4 relative z-10">
        <div className="flex items-center gap-4">
          {/* Avatar Squad */}
          <div className="relative">
            <div 
              className="w-16 h-16 rounded-2xl flex items-center justify-center font-black text-white text-2xl shadow-lg transform group-hover:rotate-3 transition-all duration-500"
              style={{ backgroundColor: t.color || '#8b5cf6' }}
            >
              {t.username.substring(0, 2).toUpperCase()}
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-bg-card border border-border-main rounded-lg flex items-center justify-center shadow-sm">
               <span className="text-[8px] font-black text-brand-primary leading-none">{t.estado}</span>
            </div>
          </div>

          <div className="space-y-0.5">
            <div className="font-black text-text-main text-xl tracking-tighter group-hover:text-brand-primary transition-colors flex items-center gap-1.5">
              @{t.username}
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            </div>
            {t.nome_completo && (
              <div className="text-[11px] text-text-muted font-bold uppercase tracking-tight truncate max-w-[180px]">
                {t.nome_completo}
              </div>
            )}
            <div className="flex items-center gap-2 mt-1.5">
              {t.partido && (
                <Badge className="bg-brand-primary/10 text-brand-primary border-none text-[8px] font-black uppercase px-2 py-0.5 rounded-md tracking-widest">
                  {t.partido}
                </Badge>
              )}
              <span className="text-[9px] text-text-muted font-mono opacity-60">
                #{t.id.substring(0, 6)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1.5">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-bg-main border border-border-main rounded-2xl shadow-inner group-hover:border-brand-primary/30 transition-colors">
            <div 
              className="w-2 h-2 rounded-full animate-pulse" 
              style={{ backgroundColor: t.color || '#333' }}
            />
            <span className="text-[10px] font-black uppercase tracking-widest" style={{ color: t.color || '#333' }}>
              {t.nivel_risco}
            </span>
          </div>
          {t.cargo && (
            <div className="text-[8px] text-text-muted font-black uppercase tracking-tighter bg-bg-main/50 px-2 py-1 rounded-lg border border-border-main/50">
              {t.cargo}
            </div>
          )}
        </div>
      </div>

      {/* KPIs Dashboard Grid */}
      <div className="mt-6 grid grid-cols-3 gap-3 relative z-10">
        <div className="bg-bg-main/40 p-3 rounded-2xl border border-border-main/50 group-hover:bg-bg-main/60 transition-colors">
          <div className="text-xl font-black text-text-main leading-none tabular-nums">{t.comentarios_odio_count}</div>
          <div className="text-[8px] font-bold text-text-muted uppercase tracking-tighter mt-1.5">Alertas (24h)</div>
        </div>
        <div className="bg-brand-primary/5 p-3 rounded-2xl border border-brand-primary/10 group-hover:bg-brand-primary/10 transition-colors">
          <div className="text-xl font-black text-brand-primary leading-none tabular-nums">{t.score_risco}%</div>
          <div className="text-[8px] font-bold text-brand-primary uppercase tracking-tighter mt-1.5">Severidade</div>
        </div>
        <div className="bg-emerald-500/5 p-3 rounded-2xl border border-emerald-500/10 group-hover:bg-emerald-500/10 transition-colors">
          <div className="text-xl font-black text-emerald-500 leading-none tabular-nums">{healthScore}%</div>
          <div className="text-[8px] font-bold text-emerald-600 uppercase tracking-tighter mt-1.5">Saúde Cívica</div>
        </div>
      </div>

      {/* Detalhamento PASA (Mini Charts) */}
      {t.breakdown && Object.keys(t.breakdown).length > 0 && (
        <div className="mt-5 space-y-2 relative z-10">
          <div className="flex justify-between items-center px-1">
            <span className="text-[8px] font-black text-text-muted uppercase tracking-[0.2em]">Padrões Detectados (MCA v2.2)</span>
            <span className="text-[8px] font-mono text-text-muted opacity-60">v85.4 neural</span>
          </div>
          <div className="flex h-2 w-full bg-bg-main/80 rounded-full overflow-hidden border border-border-main/30 p-[1px]">
            {Object.entries(t.breakdown).map(([cat, count], i) => (
              <div 
                key={cat}
                className="h-full transition-all duration-1000 first:rounded-l-full last:rounded-r-full"
                style={{ 
                  width: `${(count / totalHate) * 100}%`,
                  backgroundColor: i % 2 === 0 ? '#8b5cf6' : '#ef4444',
                  opacity: 1 - (i * 0.15)
                }}
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 px-1">
             {Object.entries(t.breakdown).slice(0, 3).map(([cat, count], i) => (
               <div key={cat} className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: i % 2 === 0 ? '#8b5cf6' : '#ef4444' }} />
                  <span className="text-[7px] font-black text-text-muted uppercase tracking-tighter">{cat.split('_')[0]} ({count})</span>
               </div>
             ))}
          </div>
        </div>
      )}

      {/* Ação Interativa no Footer */}
      <div className="mt-6 flex items-center justify-between pt-4 border-t border-border-main/50 relative z-10">
        <div className="flex items-center gap-2">
           <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
           <span className="text-[9px] font-bold text-text-muted uppercase tracking-widest">Sincronizado</span>
        </div>
        <div className="text-[9px] font-black text-brand-primary uppercase tracking-widest group-hover:translate-x-1 transition-transform flex items-center gap-1">
          Acessar dossiê detalhado ➔
        </div>
      </div>

      {/* Hover Accent Line */}
      <div className="absolute inset-x-0 bottom-0 h-1.5 bg-gradient-to-r from-brand-primary via-brand-primary/50 to-brand-primary transform scale-x-0 group-hover:scale-x-100 transition-transform duration-700" />
    </div>
  );
}
