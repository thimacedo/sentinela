'use client';

import NewsHeader from '@/components/home/NewsHeader';
import HighlightCards from '@/components/home/HighlightCards';
import EventTimeline from '@/components/home/EventTimeline';
import InsightBox from '@/components/home/InsightBox';
import CandidateProfile from '@/components/home/CandidateProfile';
import MethodologyBox from '@/components/home/MethodologyBox';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-12">
        {/* Section 1: News Header */}
        <NewsHeader
          todayHighlight={{
            title: 'Monitorando tendências de discurso',
            description: 'Sistema processando dados em tempo real de redes sociais.',
            severity: 'medium',
          }}
        />

        {/* Section 2: Highlights */}
        <HighlightCards />

        {/* Section 3: Insights & Trends */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white border-b border-slate-700 pb-4">
            🔬 Análises e Insights
          </h2>
          <InsightBox
            type="trend"
            title="Discurso em Análise"
            description="O sistema analisa padrões de discurso em tempo real para identificar anomalias."
            insight="Dados sendo coletados continuamente. Insights serão atualizados assim que houver suficiente contexto."
            metric={0}
            metricLabel="Análise em Progresso"
            confidence={0}
            sources={0}
          />
        </div>

        {/* Section 4: Timeline */}
        <EventTimeline events={[]} period="24h" />

        {/* Section 5: Candidate Profiles */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-white border-b border-slate-700 pb-4">
            👤 Candidatos Monitorados
          </h2>
          <div className="grid grid-cols-1 gap-6">
            <CandidateProfile />
          </div>
        </div>

        {/* Section 6: Methodology & About */}
        <MethodologyBox />

        {/* CTA Section */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-8 text-center">
          <h3 className="text-2xl font-bold text-white mb-3">Quer explorar mais?</h3>
          <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
            Acesse nossas ferramentas avançadas de análise forense, gere relatórios personalizados e configure alertas em tempo real.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <button className="px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-mono text-sm transition-colors">
              → Ir para Perícia Forense
            </button>
            <button className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-mono text-sm transition-colors border border-slate-600">
              → Gerar Relatório PDF
            </button>
            <button className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-mono text-sm transition-colors border border-slate-600">
              → Configurar Alertas
            </button>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-slate-700 pt-8 pb-12 text-center space-y-4">
          <p className="text-sm text-slate-500">
            Sentinela © 2024 | Transparência democrática através da análise de dados públicos
          </p>
          <div className="flex gap-6 justify-center text-xs text-slate-600">
            <button className="hover:text-slate-400">Documentação</button>
            <button className="hover:text-slate-400">Metodologia</button>
            <button className="hover:text-slate-400">Contato</button>
            <button className="hover:text-slate-400">Privacidade</button>
            <button className="hover:text-slate-400">GitHub</button>
          </div>
        </footer>
      </main>
    </div>
  );
}
