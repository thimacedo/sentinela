'use client';

import { useAlerts, useDashboardStats } from '@/hooks/useDashboardData';
import NewsHeader from '@/components/home/NewsHeader';
import HighlightCards from '@/components/home/HighlightCards';
import EventTimeline from '@/components/home/EventTimeline';
import InsightBox from '@/components/home/InsightBox';
import CandidateProfile from '@/components/home/CandidateProfile';
import MethodologyBox from '@/components/home/MethodologyBox';

export default function HomePage() {
  const { data: alerts = [] } = useAlerts(5);
  const { data: stats } = useDashboardStats();

  // Transforma alertas em eventos para a timeline
  const timelineEvents = (alerts as any[]).map((alert: any) => ({
    id: alert.id,
    timestamp: new Date(alert.data_coleta).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    candidate: alert.candidatos?.username || alert.candidato_id || 'desconhecido',
    title: alert.categoria_ia || 'Detecção de Hostilidade',
    description: alert.texto_bruto?.substring(0, 100) + '...',
    alertLevel: (alert.categoria_ia === 'CRITICO' ? 'critical' : (alert.categoria_ia === 'ELEVADO' ? 'high' : 'medium')) as 'critical' | 'high' | 'medium' | 'low',
    postsCount: 1,
    engagementMetric: Math.floor(Math.random() * 100) // Simulado por enquanto
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

        {/* Section 2: Highlights */}
        <HighlightCards />

        {/* Section 3: Insights & Trends */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-text-main border-b border-border-main pb-4">
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
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-text-main border-b border-border-main pb-4">
            👤 Perfis em Destaque
          </h2>
          <div className="grid grid-cols-1 gap-6">
            <CandidateProfile />
          </div>
        </div>

        {/* Section 6: Methodology & About */}
        <MethodologyBox />

        {/* CTA Section */}
        <div className="bg-brand-primary/10 border border-brand-primary/30 rounded-2xl p-10 text-center shadow-sm">
          <h3 className="text-3xl font-black text-text-main mb-4 tracking-tighter uppercase">Forense Avançada</h3>
          <p className="text-text-muted mb-8 max-w-2xl mx-auto leading-relaxed">
            Acesse o motor completo de investigação, mapeie redes de influência e gere dossiês técnicos detalhados com validade técnica.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button className="px-8 py-3 bg-brand-primary hover:opacity-90 text-white rounded-xl font-bold text-sm transition-all shadow-lg shadow-brand-primary/20">
              Acessar Perícia Forense
            </button>
            <button className="px-8 py-3 bg-bg-card hover:bg-bg-main text-text-main rounded-xl font-bold text-sm transition-all border border-border-main shadow-sm">
              Emitir Relatório PDF
            </button>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-border-main pt-10 pb-16 text-center space-y-6">
          <div className="flex justify-center items-center gap-2">
            <div className="w-8 h-8 bg-brand-primary rounded-lg flex items-center justify-center text-white text-xs font-black shadow-sm">S</div>
            <p className="text-lg font-black text-text-main tracking-tighter uppercase">
              Sentinela<span className="text-text-muted opacity-50 ml-1">Democrática</span>
            </p>
          </div>
          <p className="text-xs text-text-muted max-w-md mx-auto leading-relaxed opacity-60 font-mono uppercase tracking-widest">
            Tecnologia de vigilância cívica para a transparência do processo democrático brasileiro.
          </p>
          <div className="flex gap-8 justify-center text-[10px] font-bold text-text-muted uppercase tracking-tighter">
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
