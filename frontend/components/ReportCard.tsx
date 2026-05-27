import React from 'react';
import { Report } from '@/app/relatorios/page';

interface ReportCardProps {
  report: Report;
  onBuy: (reportName: string) => void;
}

export default function ReportCard({ report, onBuy }: ReportCardProps) {
  const handleClick = () => {
    // For client‑side PDF conversion, open the markdown URL in a new tab;
    // The browser can render markdown or use a JS library to convert to PDF.
    // Here we directly trigger the purchase flow which returns a signed URL.
    onBuy(report.name);
  };

  return (
    <div className="bg-white/30 backdrop-blur-lg rounded-xl shadow-lg p-4 flex flex-col items-start transition-transform hover:scale-105">
      <h2 className="text-lg font-medium mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>{report.name}</h2>
      <p className="text-sm text-gray-600 mb-4">Tipo: {report.type}</p>
      <button
        onClick={handleClick}
        className="mt-auto bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-2 rounded-md hover:opacity-90 transition"
      >
        Comprar
      </button>
    </div>
  );
}
