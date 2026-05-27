'use client';
import { useEffect, useState } from 'react';
import ReportCard from '@/components/ReportCard';
import BuyButton from '@/components/BuyButton';

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
    <div className="p-8 min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold mb-6" style={{ fontFamily: 'Inter, sans-serif' }}>Relatórios Comerciais</h1>
      {loading ? (
        <p>Carregando...</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {reports.map((r) => (
            <ReportCard key={r.name} report={r} onBuy={handleBuy} />
          ))}
        </div>
      )}
    </div>
  );
}
