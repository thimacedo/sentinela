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
        linkColor={(link: any) => link.color || 'rgba(148, 163, 184, 0.2)'}
        linkWidth={(link: any) => link.width || 1}
        onNodeClick={onNodeClick}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        backgroundColor="#0f172a"
      />
    </div>
  );
}
