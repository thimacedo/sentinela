'use client';
import { useEffect, useState } from 'react';
import ReportCard from '@/components/ReportCard';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

export interface Report {
  name: string;
  type: string;
  url: string;
}

export default function RelatoriosPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const userId = 'demo-user'; // TODO: replace with real user ID from auth

  useEffect(() => {
    async function fetchReports() {
      try {
        const res = await fetch('/api/reports');
        const data = await res.json();
        setReports(data.reports || []);
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
      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reportName, userId }),
      });
      const data = await res.json();
      if (data.downloadUrl) {
        // open visualizer with the signed URL in a new tab
        window.open(`/relatorios/visualizar?url=${encodeURIComponent(data.downloadUrl)}`, '_blank');
      } else {
        alert('Falha na compra: ' + (data.error || '')); 
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
                <ReportCard key={r.name} report={r} onBuy={handleBuy} />
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
