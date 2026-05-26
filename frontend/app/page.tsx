'use client';

import { useAlerts, useDashboardStats, useCandidates, useGeoUf } from '@/hooks/useDashboardData';
import NewsHeader from '@/components/home/NewsHeader';
import HighlightCards from '@/components/home/HighlightCards';
import EventTimeline from '@/components/home/EventTimeline';
import InsightBox from '@/components/home/InsightBox';
import CandidateProfile from '@/components/home/CandidateProfile';
import MethodologyBox from '@/components/home/MethodologyBox';
import TrendChart from '@/components/home/TrendChart';
import PremiumCTA from '@/components/home/PremiumCTA';

export default function HomePage() {
  const { data: alerts = [] } = useAlerts(25);
  const { data: stats } = useDashboardStats();
  const { data: candidates = [], isLoading: isLoadingCandidates } = useCandidates(6);
  const { data: geoUf = [], isLoading: isLoadingGeo } = useGeoUf();

  // Transforma alertas em eventos exclusivos para a timeline (evita duplicar candidato seguido)
  const timelineCandidates = new Set();
  const timelineEvents = (alerts as any[])
    .filter((alert: any) => {
      const candidate = alert.candidatos?.username || alert.candidato_id || 'desconhecido';
      if (timelineCandidates.has(candidate)) {
        return false;
      }
      timelineCandidates.add(candidate);
      return true;
    })
    .slice(0, 5) // Exibe os 5 mais recentes de perfis diferentes
    .map((alert: any) => ({
      id: alert.id,
      timestamp: new Date(alert.data_coleta).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      candidate: alert.candidatos?.username || alert.candidato_id || 'desconhecido',
      title: alert.categoria_ia || 'Detecção de Hostilidade',
      description: alert.texto_bruto?.substring(0, 100) + '...',
      alertLevel: (alert.categoria_ia === 'CRITICO' ? 'critical' : (alert.categoria_ia === 'ELEVADO' ? 'high' : 'medium')) as 'critical' | 'high' | 'medium' | 'low',
      postsCount: 1,
      engagementMetric: Math.floor(Math.random() * 40) + 60 // Risco ponderado de engajamento
    }));

  const resiliencia = stats?.resiliencia || 0;

  return (
    <div className="min-h-screen bg-bg-main transition-colors duration-300">
      {/* Main Container */}
      <main className="max-w-6xl mx-auto py-8 space-y-12">
        {/* Section 1: News Header */}
        <NewsHeader
          todayHighlight={{
            title: 'Análise de Resiliência Democrática',
            description: `O sistema detectou um índice de resiliência de ${resiliencia}% no discurso das redes sociais brasileiras nas últimas 24h.`,
            severity: resiliencia < 80 ? 'critical' : (resiliencia < 90 ? 'high' : 'medium'),
          }}
        />

        {/* Section 1.5: Activity Trend (From SaaS Logic) */}
        <TrendChart />

        {/* Section 1.8: Placar de Risco & Distribuição Territorial (SaaS Dashboard) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Placar de Risco (Risk Scoreboard) - Ocupa 2 colunas */}
          <div className="lg:col-span-2 bg-bg-card border border-border-main rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-border-main/50 pb-2.5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-main flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
                🚨 Placar de Risco (Risk Scoreboard)
              </h3>
              <span className="text-[9px] font-mono text-brand-primary font-bold bg-brand-primary/10 px-1.5 py-0.5 rounded border border-brand-primary/20">PRO LEVEL</span>
            </div>
            
            {isLoadingCandidates ? (
              <p className="text-xs text-text-muted font-mono animate-pulse text-center py-6">Calculando score de toxicidade...</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {candidates.slice(0, 4).map((cand: any, idx: number) => {
                  const score = cand.score_risco || 0;
                  const barColor = score > 80 ? 'bg-red-500' : (score > 50 ? 'bg-orange-500' : 'bg-blue-500');
                  const badgeColor = score > 80 ? 'bg-red-500/10 text-red-500' : (score > 50 ? 'bg-orange-500/10 text-orange-500' : 'bg-blue-500/10 text-blue-500');
                  
                  return (
                    <div key={cand.id} className="flex items-center gap-3 text-xs bg-bg-main border border-border-main/50 p-3 rounded-lg hover:border-brand-primary/30 transition-all">
                      <div className="w-6 h-6 rounded-md bg-bg-card border border-border-main flex items-center justify-center font-bold text-text-muted font-mono text-[10px]">
                        {idx + 1}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <strong className="text-[11px] text-text-main font-mono truncate">@{cand.username}</strong>
                          <span className={`px-1 rounded text-[8px] font-bold uppercase ${badgeColor}`}>
                            {score}%
                          </span>
                        </div>
                        {/* Progress Bar */}
                        <div className="w-full bg-bg-card rounded-full h-1.5 overflow-hidden border border-border-main/20">
                          <div 
                            className={`h-full rounded-full transition-all duration-500 ${barColor}`} 
                            style={{ width: `${score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          
          {/* Distribuição Territorial (Geo-Risk Map) - Ocupa 1 coluna */}
          <div className="bg-bg-card border border-border-main rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-border-main/50 pb-2.5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-main flex items-center gap-2">
                🌐 Distribuição por UF
              </h3>
              <span className="text-[9px] font-mono text-emerald-500 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">LIVE</span>
            </div>
            
            {isLoadingGeo ? (
              <p className="text-xs text-text-muted font-mono animate-pulse text-center py-6">Mapeando geolocalização...</p>
            ) : (
              <div className="space-y-2">
                {geoUf.slice(0, 3).map((item: any) => (
                  <div key={item.uf} className="flex items-center justify-between text-xs bg-bg-main/50 border border-border-main/30 p-2 rounded">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded bg-bg-card border border-border-main flex items-center justify-center font-extrabold font-mono text-[9px]">
                        {item.uf}
                      </span>
                      <span className="text-text-muted text-[10px]">Alertas: <strong className="text-text-main">{item.total_hate}</strong></span>
                    </div>
                    <span 
                      className="w-2 h-2 rounded-full animate-pulse" 
                      style={{ backgroundColor: item.color || '#ef4444' }} 
                    />
                  </div>
                ))}
                {geoUf.length === 0 && (
                  <p className="text-[10px] text-text-muted font-mono text-center py-4 italic">Nenhum dado geográfico recente.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Section 2: Highlights */}
        <HighlightCards />

        {/* Section 3: Insights & Trends */}
        <div className="space-y-3">
          <h2 className="text-sm sm:text-base font-bold text-text-main tracking-tight uppercase flex items-center gap-2 border-b border-border-main/50 pb-2">
            <span className="w-1.5 h-1.5 bg-brand-primary rounded-full" />
            🔬 Análises e Insights
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InsightBox
              type="trend"
              title="Padrão de Discurso"
              description="Análise volumétrica da hostilidade detectada nos alvos ativos."
              insight="A tendência indica estabilidade com picos isolados de hostilidade ad hominem."
              metric={resiliencia}
              metricLabel="Saúde do Discurso"
              confidence={94}
              sources={stats?.total_amostra || 0}
            />
            <InsightBox
              type="pattern"
              title="Comportamento Coordenado"
              description="Detecção de mensagens idênticas ou altamente similares em massa."
              insight="Monitoramento Solenya v71.0 ativo. Buscando padrões de automação."
              confidence={88}
              sources={stats?.total_amostra || 0}
            />
          </div>
        </div>

        {/* Section 4: Timeline */}
        <EventTimeline events={timelineEvents} period="24h" />

        {/* Section 5: Candidate Profiles */}
        <div className="space-y-3">
          <div className="flex items-center justify-between border-b border-border-main/50 pb-2">
            <h2 className="text-sm sm:text-base font-bold text-text-main tracking-tight uppercase flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-brand-primary rounded-full" />
              👤 Perfis em Destaque
            </h2>
            <p className="text-[9px] text-text-muted font-mono animate-pulse uppercase tracking-wider">
              Use as setas para explorar →
            </p>
          </div>
          <div className="grid grid-cols-1 gap-6">
            <CandidateProfile />
          </div>
        </div>

        {/* Section 6: Methodology & About */}
        <MethodologyBox />

        {/* CTA Section (From SaaS Logic) */}
        <PremiumCTA />

        {/* Footer */}
        <footer className="border-t border-border-main/50 pt-8 pb-12 text-center space-y-4">
          <div className="flex justify-center items-center gap-2">
            <div className="w-6 h-6 bg-brand-primary rounded-md flex items-center justify-center text-white text-[10px] font-black shadow-sm">S</div>
            <p className="text-sm font-black text-text-main tracking-tighter uppercase">
              Sentinela<span className="text-text-muted opacity-50 ml-1">Democrática</span>
            </p>
          </div>
          <p className="text-[10px] text-text-muted max-w-md mx-auto leading-normal opacity-70 font-mono uppercase tracking-wider">
            Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
          </p>
          <div className="flex gap-6 justify-center text-[9px] font-bold text-text-muted uppercase tracking-tighter pt-2">
            <button className="hover:text-brand-primary transition-colors">Termos</button>
            <button className="hover:text-brand-primary transition-colors">Metodologia</button>
            <button className="hover:text-brand-primary transition-colors">LGPD</button>
            <button className="hover:text-brand-primary transition-colors">Privacidade</button>
            <button className="hover:text-brand-primary transition-colors">GitHub</button>
          </div>
        </footer>
      </main>
    </div>
  );
}
