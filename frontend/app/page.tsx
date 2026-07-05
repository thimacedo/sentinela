'use client';
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

// Interfaces para tipagem forte
interface Alert {
  id: string;
  data_coleta: string;
  candidatos?: {
    username: string;
  };
  candidato_id?: string;
  categoria_ia: 'CRITICO' | 'ELEVADO' | 'MEDIO' | 'BAIXO' | string;
  texto_bruto?: string;
}

interface DashboardStats {
  resiliencia?: number;
  total_amostra?: number;
  total_alertas?: number;
  total_monitorados?: number;
}

interface TimelineEvent {
  id: string;
  timestamp: string;
  candidate: string;
  title: string;
  description: string;
  alertLevel: 'critical' | 'high' | 'medium' | 'low';
  postsCount: number;
  engagementMetric: number;
}

export default function HomePage() {
  const [period, setPeriod] = useState<'24h' | '7d' | '30d'>('24h');
  const { data: alerts = [] } = useAlerts(5);
  const { data: stats } = useDashboardStats();

  const timelineEvents: TimelineEvent[] = (alerts as Alert[]).map((alert: Alert) => ({
    id: alert.id,
    timestamp: new Date(alert.data_coleta).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    candidate: alert.candidatos?.username || alert.candidato_id || 'desconhecido',
    title: alert.categoria_ia || 'Detecção de Hostilidade',
    description: alert.texto_bruto?.substring(0, 100) + '...',
    alertLevel: (alert.categoria_ia === 'CRITICO' ? 'critical' : (alert.categoria_ia === 'ELEVADO' ? 'high' : 'medium')) as 'critical' | 'high' | 'medium' | 'low',
    postsCount: 1,
    engagementMetric: 50
  }));

  const resiliencia = (stats as DashboardStats)?.resiliencia || 0;

  return (
    <div className="min-h-screen bg-bg-main transition-colors duration-300">
      <main className="max-w-6xl mx-auto py-10 space-y-20 px-4 sm:px-6 lg:px-8">
        <NewsHeader />
        <EventTimeline events={timelineEvents} period={period} onPeriodChange={setPeriod} />
        <TrendChart />
        <AdSenseSlot adSlot="2020882637" format="horizontal" />
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
              sources={(stats as DashboardStats)?.total_amostra || 0}
            />
            <InsightBox
              type="pattern"
              title="Comportamento Coordenado"
              description="Detecção de mensagens idênticas ou altamente similares em massa."
              insight="Monitoramento Solenya v71.0 ativo. Buscando padrões de automação."
              confidence={88}
              sources={(stats as DashboardStats)?.total_amostra || 0}
            />
          </div>
        </div>
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
        <MethodologyBox />
        <AdSenseSlot adSlot="2020882637" format="horizontal" />
        <PremiumCTA />
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