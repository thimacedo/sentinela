'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { useAlerts, useDashboardStats } from '@/hooks/useDashboardData';
import NewsHeader from '@/components/home/NewsHeader';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import Link from 'next/link';
import EventTimeline from '@/components/home/EventTimeline';
import InsightBox from '@/components/home/InsightBox';
import CandidateProfile from '@/components/home/CandidateProfile';
import MethodologyBox from '@/components/home/MethodologyBox';
import TrendChart from '@/components/home/TrendChart';
import PremiumCTA from '@/components/home/PremiumCTA';

export default function HomePage() {
  const [period, setPeriod] = useState<'24h' | '7d' | '30d'>('24h');
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
    engagementMetric: 50 // Simulado fixo por enquanto
  }));

  const resiliencia = stats?.resiliencia || 0;

  return (
    <div className="min-h-screen bg-bg-main transition-colors duration-300">
      {/* Main Container */}
      <main className="max-w-6xl mx-auto py-10 space-y-20 px-4 sm:px-6 lg:px-8">
        {/* Section 1: News Header */}
        <NewsHeader />

        {/* Timeline Movida para o Topo com Controle de Período */}
        <EventTimeline 
          events={timelineEvents} 
          period={period} 
          onPeriodChange={setPeriod}
        />

        {/* Section 1.5: Activity Trend (From SaaS Logic) */}
        <TrendChart />

        {/* Section 2 removida para evitar redundância de Destaques e Linha do Tempo */}
        {/* Anúncio AdSense */}
        <AdSenseSlot adSlot="2020882637" format="horizontal" />

        {/* Section 3: Insights & Trends */}
        <div className="space-y-8">
          <div className="flex items-center gap-3 border-b border-border-main pb-4">
            <span className="text-3xl">🔬</span>
            <h2 className="text-3xl font-black text-text-main tracking-tight uppercase">Análises e Insights</h2>
          </div>
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



        {/* Section 5: Candidate Profiles */}
        <div className="space-y-8">
          <div className="flex items-center justify-between border-b border-border-main pb-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">👤</span>
              <h2 className="text-3xl font-black text-text-main tracking-tight uppercase">Perfis em Destaque</h2>
            </div>
            <p className="text-[10px] text-text-muted font-mono font-bold uppercase tracking-widest hidden sm:block">
              Use as setas para explorar →
            </p>
          </div>
          <div className="grid grid-cols-1 gap-6">
            <CandidateProfile />
          </div>
        </div>

        {/* Section 6: Methodology & About */}
        <MethodologyBox />

        {/* Anúncio AdSense Bottom */}
        <AdSenseSlot adSlot="2020882637" format="horizontal" />

        {/* CTA Section (From SaaS Logic) */}
        <PremiumCTA />

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
          <div className="flex gap-8 justify-center text-xs font-bold text-text-muted uppercase tracking-tighter">
            <Link href="/termos" className="hover:text-brand-primary transition-colors">Termos</Link>
            <Link href="/metodologia" className="hover:text-brand-primary transition-colors">Metodologia</Link>
            <Link href="/lgpd" className="hover:text-brand-primary transition-colors">LGPD</Link>
            <Link href="/privacidade" className="hover:text-brand-primary transition-colors">Privacidade</Link>
            <Link href="https://github.com/THIAGO/sentinela" className="hover:text-brand-primary transition-colors" target="_blank" rel="noopener noreferrer">GitHub</Link>
          </div>
        </footer>
      </main>
    </div>
  );
}
