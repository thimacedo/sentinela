'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

function parseMarkdown(md: string): string {
  // Limpa retornos de carro
  let html = md.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  // Tabelas markdown para HTML
  const lines = html.split('\n');
  let inTable = false;
  let tableHtml = '';
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      if (!inTable) {
        inTable = true;
        tableHtml = '<div class="overflow-x-auto my-6"><table class="min-w-full border-collapse border border-gray-200 shadow-sm rounded-lg overflow-hidden">';
      }
      
      const cells = line.split('|').map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
      
      // Verifica se é linha divisória | --- | --- |
      if (cells.every(c => /^:-{1,}:|:-{1,}|-{1,}:|-{1,}$/.test(c))) {
        continue;
      }
      
      // Se for a primeira linha (e a próxima for divisória), renderiza thead
      const isHeader = i < lines.length - 1 && lines[i+1].trim().startsWith('|') && lines[i+1].trim().includes('---');
      
      tableHtml += isHeader ? '<thead class="bg-gray-100 text-gray-700 font-semibold">' : '<tr>';
      cells.forEach(cell => {
        if (isHeader) {
          tableHtml += `<th class="border border-gray-200 px-4 py-3 text-left text-sm font-semibold">${cell}</th>`;
        } else {
          tableHtml += `<td class="border border-gray-200 px-4 py-3 text-sm text-gray-700 bg-white">${cell}</td>`;
        }
      });
      tableHtml += isHeader ? '</thead><tbody>' : '</tr>';
    } else {
      if (inTable) {
        inTable = false;
        tableHtml += '</tbody></table></div>';
        lines[i] = tableHtml + '\n' + line;
        tableHtml = '';
      }
    }
  }
  if (inTable) {
    tableHtml += '</tbody></table></div>';
    lines[lines.length - 1] = tableHtml;
  }
  html = lines.join('\n');

  // Títulos
  html = html.replace(/^### (.*$)/gim, '<h3 class="text-lg font-bold text-gray-800 mt-6 mb-2">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold text-gray-800 mt-8 mb-4 border-b pb-2">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 class="text-3xl font-extrabold text-gray-900 mt-4 mb-6">$1</h1>');

  // Negrito e Itálico
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-950">$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');

  // Listas não ordenadas
  const lines2 = html.split('\n');
  let inList = false;
  for (let i = 0; i < lines2.length; i++) {
    const line = lines2[i].trim();
    if (line.startsWith('- ') || line.startsWith('* ')) {
      const content = line.substring(2);
      if (!inList) {
        inList = true;
        lines2[i] = '<ul class="list-disc pl-6 my-4 space-y-2 text-gray-700">\n<li>' + content + '</li>';
      } else {
        lines2[i] = '<li>' + content + '</li>';
      }
    } else {
      if (inList) {
        inList = false;
        lines2[i] = '</ul>\n' + lines2[i];
      }
    }
  }
  if (inList) {
    lines2[lines2.length - 1] = lines2[lines2.length - 1] + '\n</ul>';
  }
  html = lines2.join('\n');

  // Parágrafos
  const paragraphs = html.split('\n\n');
  html = paragraphs.map(p => {
    const trimmed = p.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('<h') || trimmed.startsWith('<ul') || trimmed.startsWith('<div') || trimmed.startsWith('<table') || trimmed.startsWith('</') || trimmed.startsWith('<tr>') || trimmed.startsWith('<li')) {
      return trimmed;
    }
    return `<p class="my-4 text-gray-700 leading-relaxed text-sm md:text-base">${trimmed}</p>`;
  }).join('\n');

  return html;
}

function VisualizarContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const url = searchParams.get('url');
  
  const [markdown, setMarkdown] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!url) {
      setError('URL do relatório não fornecida.');
      setLoading(false);
      return;
    }

    async function loadReport(targetUrl: string) {
      try {
        const res = await fetch(targetUrl);
        if (!res.ok) {
          throw new Error('Falha ao baixar o arquivo do relatório.');
        }
        const text = await res.text();
        setMarkdown(text);
      } catch (e: any) {
        setError(e.message || 'Erro ao carregar o relatório.');
      } finally {
        setLoading(false);
      }
    }

    loadReport(url);
  }, [url]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600 font-medium">Carregando relatório...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
        <div className="bg-white/80 backdrop-blur-md rounded-xl p-8 shadow-lg max-w-md w-full border border-red-100 text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Erro ao Carregar Relatório</h2>
          <p className="text-gray-600 mb-6 text-sm">{error}</p>
          <button
            onClick={() => router.push('/relatorios')}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition"
          >
            Voltar para Relatórios
          </button>
        </div>
      </div>
    );
  }

  const htmlContent = parseMarkdown(markdown);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 pb-16">
      {/* Barra de Ações - Oculta na Impressão */}
      <div className="print:hidden sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200 py-4 px-6 md:px-12 flex justify-between items-center shadow-sm">
        <button
          onClick={() => router.push('/relatorios')}
          className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-2 text-sm bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-lg transition"
        >
          ← Voltar
        </button>
        <button
          onClick={handlePrint}
          className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-5 py-2 rounded-lg font-medium hover:opacity-90 transition flex items-center gap-2 text-sm shadow-md"
        >
          📥 Exportar para PDF / Imprimir
        </button>
      </div>

      {/* Container do Relatório */}
      <div className="max-w-4xl mx-auto mt-8 p-8 md:p-12 bg-white shadow-xl rounded-2xl border border-gray-100 print:shadow-none print:border-none print:mt-0 print:p-0">
        {/* Cabeçalho do Relatório Timbrado */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b-2 border-indigo-600 pb-6 mb-8 gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-gray-900" style={{ fontFamily: 'Inter, sans-serif' }}>
              SENTINELA
            </h1>
            <p className="text-xs text-gray-500 uppercase tracking-widest mt-1 font-semibold">
              Plataforma Democrática de Análise de Discurso
            </p>
          </div>
          <div className="text-left md:text-right text-xs md:text-sm text-gray-500 font-medium">
            <p>Emissão: {new Date().toLocaleDateString('pt-BR')}</p>
            <p>Status: Original Assinado</p>
            <p>ID do Usuário: demo-user</p>
          </div>
        </div>

        {/* Conteúdo Dinâmico Renderizado */}
        <div 
          className="prose max-w-none prose-indigo"
          dangerouslySetInnerHTML={{ __html: htmlContent }} 
        />

        {/* Rodapé de Validação */}
        <div className="mt-16 border-t border-gray-200 pt-6 flex flex-col md:flex-row justify-between items-center text-xs text-gray-400 gap-4">
          <p>© {new Date().getFullYear()} Sentinela. Todos os direitos reservados.</p>
          <p className="font-semibold text-gray-500">Documento gerado em conformidade com o Protocolo PASA v83.5</p>
        </div>
      </div>
    </div>
  );
}

export default function VisualizarRelatorioPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600 font-medium">Carregando visualizador...</p>
      </div>
    }>
      <VisualizarContent />
    </Suspense>
  );
}
