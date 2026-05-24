'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSystemInformation } from '@/hooks/useSystemInformation';

export default function DashboardStats() {
  const { data: stats, isLoading } = useSystemInformation();

  const displayStats = stats || {
    total_monitorados: 0,
    total_alertas: 0,
    total_amostra: 0,
    resiliencia: 0,
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-500/50 transition-all duration-300 group">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-500 text-[10px] uppercase font-bold tracking-widest flex justify-between">
            Alvos Ativos
            <span className="text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity">●</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-slate-100">{isLoading ? "..." : displayStats.total_monitorados}</p>
          <p className="text-[10px] text-slate-600 mt-1 font-mono uppercase">Perfis em monitoramento</p>
        </CardContent>
      </Card>
      
      <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-500/50 transition-all duration-300 group">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-500 text-[10px] uppercase font-bold tracking-widest flex justify-between">
            Indícios Detectados
            <span className="text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">▲</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-slate-100">{isLoading ? "..." : displayStats.total_alertas.toLocaleString()}</p>
          <p className="text-[10px] text-slate-600 mt-1 font-mono uppercase">Casos para análise</p>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-500/50 transition-all duration-300 group">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-500 text-[10px] uppercase font-bold tracking-widest flex justify-between">
            Volume Analisado
            <span className="text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity">◆</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-slate-100">{isLoading ? "..." : displayStats.total_amostra.toLocaleString()}</p>
          <p className="text-[10px] text-slate-600 mt-1 font-mono uppercase">Comentários extraídos</p>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 hover:border-emerald-500/50 transition-all duration-300 group">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-500 text-[10px] uppercase font-bold tracking-widest flex justify-between">
            Resiliência
            <span className="text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity">✓</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-emerald-500">{isLoading ? "..." : `${displayStats.resiliencia}%`}</p>
          <p className="text-[10px] text-slate-600 mt-1 font-mono uppercase">Saúde da rede social</p>
        </CardContent>
      </Card>
    </div>
  );
}
