'use client';
import React, { useRef, useEffect, useState } from 'react';

// Wrapper seguro para evitar erro de SSR no Next.js ao usar bibliotecas que dependem de window/canvas
export default function ForceGraphWrapper({ graphData, onNodeClick }: { graphData: any, onNodeClick?: (node: any) => void }) {
  const [ForceGraph2D, setForceGraph2D] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    // Dynamic import to avoid SSR issues
    import('react-force-graph-2d').then((module) => {
      setForceGraph2D(() => module.default);
    });
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      setDimensions({ width: clientWidth, height: clientHeight || 500 });
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({ 
          width: containerRef.current.clientWidth, 
          height: containerRef.current.clientHeight || 500 
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!ForceGraph2D) {
    return <div className="w-full h-full flex items-center justify-center text-text-muted animate-pulse font-mono text-[10px] uppercase">Inicializando Motor de Renderização de Grafos...</div>;
  }

  return (
    <div ref={containerRef} className="w-full h-full min-h-[500px] bg-[#0f172a] rounded-xl overflow-hidden cursor-crosshair">
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeLabel="id"
        nodeColor={(node: any) => node.color || '#3b82f6'}
        nodeVal={(node: any) => node.val || 1}
        linkColor={(link: any) => link.color || 'rgba(255, 255, 255, 0.15)'}
        linkWidth={(link: any) => link.width || 1}
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          // Desenha o círculo/nó (Neon Glow se tiver val alto)
          const nodeSize = node.val ? Math.sqrt(node.val) * 2.5 : 4;
          
          ctx.beginPath();
          ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI, false);
          ctx.fillStyle = node.color || '#00e5ff';
          ctx.fill();

          // Desenha Glow Edge em nós de alto impacto
          if (node.isAttacker) {
            ctx.strokeStyle = 'rgba(255, 0, 85, 0.4)';
            ctx.lineWidth = 2 / globalScale;
            ctx.stroke();
          }

          // Se o zoom estiver distante, evitamos o emaranhado de texto
          if (globalScale >= 2.0) {
            const label = node.id;
            const fontSize = 10 / globalScale;
            ctx.font = `bold ${fontSize}px Sans-Serif`;
            const textWidth = ctx.measureText(label).width;
            
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            // Desenha um fundo escuro abaixo do nó para o texto aparecer limpo
            const xPos = node.x - bckgDimensions[0] / 2;
            const yPos = node.y + nodeSize + 1;
            
            ctx.fillStyle = 'rgba(2, 6, 23, 0.7)'; // escuro transparente
            ctx.beginPath();
            ctx.roundRect(xPos, yPos, bckgDimensions[0], bckgDimensions[1], 1);
            ctx.fill();

            // Escreve o nome
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = '#f8fafc'; // texto branco claro
            ctx.fillText(label, node.x, yPos + (fontSize * 0.1));
            
            node.__bckgDimensions = bckgDimensions; 
          }
        }}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          ctx.fillStyle = color;
          const nodeSize = node.val ? Math.sqrt(node.val) * 2.5 : 4;
          ctx.beginPath();
          ctx.arc(node.x, node.y, nodeSize + 2, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
        onNodeClick={onNodeClick}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        backgroundColor="#0f172a"
      />
    </div>
  );
}
