'use client';
import { useEffect, useState } from 'react';
import ReportCard from '@/components/ReportCard';
import AdSenseSlot from '@/components/ads/AdSenseSlot';
import { API_BASE_URL } from '@/lib/api';

export interface Report {
  name: string;
  type: string;
  url: string;
  candidatoId: string;
}

export default function RelatoriosPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const userId = typeof window !== 'undefined'
    ? localStorage.getItem('sentinela_user_id') || 'guest_user'
    : 'guest_user';

  useEffect(() => {
    async function fetchReports() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/dossiers`);
        const data = await res.json();
        const mapped = (data || []).map((d: any) => ({
          name: `Dossiê @${d.candidato_id || 'alvo'}`,
          type: 'pdf',
          url: d.arquivo_path || '',
          candidatoId: d.candidato_id || '',
        }));
        setReports(mapped);
      } catch (e) {
        console.error('Erro ao obter relatórios', e);
      } finally {
        setLoading(false);
      }
    }
    fetchReports();
  }, []);

  const handleBuy = async (reportName: string) => {
    try {
      const selected = reports.find((r) => r.name === reportName);
      if (!selected?.candidatoId) {
        alert('Falha na emissão: candidato inválido para este dossiê.');
        return;
      }
      const res = await fetch(`${API_BASE_URL}/api/v1/dossiers/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidato_id: selected.candidatoId, user_id: userId, modules: ['base'] }),
      });
      const data = await res.json();
      if (data.pdf_url) {
        const targetUrl = data.pdf_url.startsWith('http') ? data.pdf_url : `${API_BASE_URL}${data.pdf_url}`;
        window.open(targetUrl, '_blank');
      } else {
        alert('Falha na compra: ' + (data.detail || data.error || ''));
      }
    } catch (e) {
      console.error('Erro ao comprar relatório', e);
    }
  };

  return (
    <div className="min-h-screen bg-bg-main p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-text-main tracking-tight uppercase">
              Dossiês de Inteligência
            </h1>
            <div className="hidden md:inline-flex items-center px-2 py-0.5 bg-brand-primary/10 text-brand-primary border border-brand-primary/20 rounded-full text-[10px] font-black uppercase tracking-widest">
              Arquivo Confidencial
            </div>
          </div>
          <p className="text-xs text-text-muted hidden md:block max-w-md text-right">
            Acesso aos relatórios analíticos. O desbloqueio consome Créditos de Inteligência (CI).
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce" />
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce delay-100" />
              <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce delay-200" />
              <span className="text-[10px] font-black text-brand-primary uppercase tracking-widest ml-2">Acessando Servidor Seguro...</span>
            </div>
          </div>
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {reports.map((r) => (
                <ReportCard key={`${r.name}-${r.candidatoId}`} report={r} onBuy={handleBuy} />
              ))}
            </div>
            <div className="mt-8">
              <AdSenseSlot adSlot="2020882637" format="horizontal" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
