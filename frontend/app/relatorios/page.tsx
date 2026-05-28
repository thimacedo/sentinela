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
        <div className="mb-12 border-b border-border-main pb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-primary/10 text-brand-primary border border-brand-primary/20 rounded-full mb-6 text-[10px] font-black uppercase tracking-widest">
            Arquivo Confidencial
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-text-main tracking-tighter mb-4">
            Dossiês de Inteligência
          </h1>
          <p className="text-sm text-text-muted max-w-2xl leading-relaxed">
            Acesso aos relatórios periciais gerados pela plataforma. O desbloqueio de novos documentos consome Créditos de Inteligência (CI) devido ao uso intensivo de exportação e processamento forense.
          </p>
        </div>

        <div className="mb-8">
          <AdSenseSlot adSlot="2020882637" format="horizontal" />
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
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {reports.map((r) => (
              <ReportCard key={r.name} report={r} onBuy={handleBuy} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
