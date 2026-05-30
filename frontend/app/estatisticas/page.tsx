'use client';

import React, { useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Sector, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { useDemographics } from '@/hooks/useDashboardData';
import { ShieldAlert, Crosshair, TrendingUp, Activity, FileText, Users, Filter, BarChart3, AlertTriangle, Sparkles, MapPin, Target, EyeOff } from 'lucide-react';
import AdSenseSlot from '@/components/ads/AdSenseSlot';

// --- MOCK DATA PARA OS NOVOS GRÁFICOS DE MARKETING (GATILHOS) ---
const trendData = [
  { day: '01', organico: 120, bot: 20 }, { day: '05', organico: 130, bot: 80 },
  { day: '10', organico: 110, bot: 450 }, { day: '15', organico: 180, bot: 1200 },
  { day: '20', organico: 250, bot: 3100 }, { day: '25', organico: 300, bot: 4800 },
  { day: 'Hoje', organico: 450, bot: 8900 }
];

const radarData = [
  { subject: 'Desinformação', A: 120, fullMark: 150 },
  { subject: 'Difamação', A: 98, fullMark: 150 },
  { subject: 'Ação Coordenada (Bots)', A: 140, fullMark: 150 },
  { subject: 'Ataque à Reputação', A: 99, fullMark: 150 },
  { subject: 'Hostilidade', A: 85, fullMark: 150 },
  { subject: 'Engajamento Inautêntico', A: 135, fullMark: 150 },
];

const indiciosData = [
  { name: 'Danos à Imagem', value: 450, fill: '#f43f5e' },
  { name: 'Hostilidade Percebida', value: 120, fill: '#ef4444' },
  { name: 'Volume Coordenado', value: 890, fill: '#8b5cf6' },
  { name: 'Perfis Inautênticos', value: 340, fill: '#3b82f6' },
];

// --- COMPONENTES AUXILIARES ---
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-bg-card/90 border border-border-main p-4 rounded-2xl shadow-2xl backdrop-blur-xl ring-1 ring-white/10">
        <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2">{label || payload[0]?.payload?.name || 'Métrica'}</p>
        {payload.map((item: any, idx: number) => (
          <div key={idx} className="flex items-center gap-3 mb-1 last:mb-0">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color || item.payload.fill || '#10b981' }} />
            <p className="text-lg font-black text-text-main tabular-nums leading-none">
              {item.value} <span className="text-[10px] text-text-muted font-normal uppercase">{item.name !== 'value' ? item.name : 'registros'}</span>
            </p>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, value } = props;
  return (
    <g>
      <text x={cx} y={cy - 12} dy={8} textAnchor="middle" fill={fill} className="font-bold uppercase tracking-widest" style={{ fontSize: '10px' }}>
        {payload.name}
      </text>
      <text x={cx} y={cy + 12} dy={8} textAnchor="middle" fill="#94a3b8" className="font-black tabular-nums" style={{ fontSize: '18px' }}>
        {value}
      </text>
      <Sector cx={cx} cy={cy} innerRadius={innerRadius} outerRadius={outerRadius + 6} startAngle={startAngle} endAngle={endAngle} fill={fill} className="transition-all duration-300 drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]" />
      <Sector cx={cx} cy={cy} startAngle={startAngle} endAngle={endAngle} innerRadius={outerRadius + 10} outerRadius={outerRadius + 14} fill={fill} opacity={0.3} />
    </g>
  );
};

export default function DemographicsMarketingPage() {
  const { data, isLoading } = useDemographics();
  const [activeIndex, setActiveIndex] = useState(0);

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto space-y-8 py-6">
        <div className="text-center py-32 flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-red-500/30 border-t-red-500 rounded-full animate-spin" />
          <div className="text-text-main font-bold animate-pulse font-mono text-[12px] uppercase tracking-widest">
            Mapeando Redes Neurais e Compilando Informações Analíticas...
          </div>
        </div>
      </div>
    );
  }

  const { sexo = [], partido = [], estado = [], ideologia = [], top_alvos = [] } = data || {};
  const vipTargets = top_alvos.slice(0, 3);
  const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e'];

  const onPieEnter = (_: any, index: number) => setActiveIndex(index);

  return (
    <div className="max-w-7xl mx-auto space-y-8 py-8 px-4 sm:px-6">
      
      {/* HEADER DE MARKETING (Autoridade & Problema/Solução) */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-8 border-b border-border-main pb-8">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-500/10 text-red-500 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 border border-red-500/20">
            <Activity className="w-3 h-3 animate-pulse" /> Monitoramento Ativo | Alerta de Volume
          </div>
          <h1 className="text-4xl sm:text-5xl font-black text-text-main tracking-tight uppercase leading-tight">
            Radiografia do <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-pink-500">Ruído Oculto</span>
          </h1>
          <p className="text-sm sm:text-base text-text-muted mt-4 font-medium leading-relaxed">
            As interações não são apenas orgânicas, há padrões de comportamento coordenado atuando contra sua imagem. 
            Nossa Inteligência Analítica identifica as fontes. <strong>Transforme o ruído em um relatório técnico documentado</strong> com um clique.
          </p>
        </div>
        <div className="flex-shrink-0 flex flex-col gap-3">
          <button className="bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-black uppercase tracking-widest px-8 py-4 rounded-xl shadow-[0_0_20px_rgba(220,38,38,0.3)] hover:shadow-[0_0_30px_rgba(220,38,38,0.5)] transition-all duration-300 hover:-translate-y-1 flex items-center justify-center gap-3">
            <FileText className="w-5 h-5" /> Gerar Dossiê Analítico
          </button>
          <p className="text-[10px] text-center text-text-muted font-bold uppercase tracking-widest">Apenas 350 CI por relatório</p>
        </div>
      </div>

      {/* GATILHO DE PROVA SOCIAL E ESCASSEZ DE REPUTAÇÃO (Cards VIP) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {vipTargets.map((vip: any, idx: number) => (
          <div key={vip.name} className="bg-bg-card border border-red-500/20 rounded-3xl p-6 shadow-lg hover:shadow-red-500/10 transition-all duration-300 hover:-translate-y-2 relative overflow-hidden group glass-card">
             <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:bg-red-500/20 transition-all duration-500" />
             <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-orange-500" />
             
             <div className="flex items-center gap-4 relative z-10 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center font-black text-red-500 text-xl shadow-inner">
                  #{idx + 1}
                </div>
                <div>
                  <div className="text-[9px] font-bold text-red-500 uppercase tracking-widest flex items-center gap-1.5 mb-0.5">
                    <Crosshair className="w-3 h-3" /> Foco Inautêntico
                  </div>
                  <div className="font-black text-text-main text-xl tracking-tight">@{vip.name}</div>
                </div>
             </div>
             <div className="flex items-end justify-between relative z-10 mt-4">
               <div>
                 <div className="text-[10px] text-text-muted font-bold uppercase tracking-widest mb-1">Registros de Origem</div>
                 <div className="text-4xl font-black text-text-main tabular-nums tracking-tighter">{vip.value}</div>
               </div>
               <div className="bg-red-500/10 text-red-500 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg border border-red-500/20 flex items-center gap-1">
                 <ShieldAlert className="w-3 h-3" /> Mapeado
               </div>
             </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        
        {/* NOVO GRÁFICO: URGÊNCIA (Evolução de Ameaças - Milícia Digital) */}
        <div className="lg:col-span-2 bg-bg-card border border-border-main rounded-3xl p-8 shadow-md glass-card relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5"><TrendingUp className="w-64 h-64" /></div>
          <div className="mb-8 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-500/10 text-purple-500 rounded-full text-[10px] font-black uppercase tracking-widest mb-3">
              <EyeOff className="w-3 h-3" /> Identificação de Comportamento Inautêntico
            </div>
            <h2 className="text-2xl font-black text-text-main uppercase tracking-tight">Evolução do Volume Anômalo (30 Dias)</h2>
            <p className="text-xs text-text-muted mt-2 max-w-2xl">
              Compare a atividade de interações regulares com o volume de engajamento inautêntico. 
              Picos da linha roxa representam indícios de campanhas coordenadas prontas para serem mapeadas.
            </p>
          </div>
          <div className="h-[350px] w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorBot" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorOrg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.5}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={10} fontWeight="bold" />
                <YAxis hide />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="organico" name="Interação Regular" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorOrg)" />
                <Area type="monotone" dataKey="bot" name="Volume Coordenado (Inautêntico)" stroke="#8b5cf6" strokeWidth={4} fillOpacity={1} fill="url(#colorBot)" activeDot={{ r: 8, fill: "#8b5cf6", stroke: "#fff", strokeWidth: 2 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* NOVO GRÁFICO: CURIOSIDADE (Radar de Vulnerabilidade) */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/10 rounded-xl"><Target className="w-5 h-5 text-orange-500" /></div>
              <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Vetor de Incidência</h2>
            </div>
            <p className="text-[10px] text-text-muted mt-2 font-bold uppercase">Onde a narrativa adversária está focando</p>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#334155" opacity={0.3} />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }} />
                <PolarRadiusAxis angle={30} domain={[0, 150]} tick={false} axisLine={false} />
                <Radar name="Intensidade Analítica" dataKey="A" stroke="#f59e0b" strokeWidth={2} fill="#f59e0b" fillOpacity={0.3} />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* NOVO GRÁFICO: RESOLUÇÃO DE PROBLEMA (Materialidade Criminal -> Sistematização de Indícios) */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="mb-4 relative z-10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/10 rounded-xl"><FileText className="w-5 h-5 text-red-500" /></div>
              <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Sistematização de Indícios</h2>
            </div>
            <p className="text-[10px] text-text-muted mt-2 font-bold uppercase">Apontamentos qualificados prontos para Dossiê</p>
          </div>
          <div className="h-[260px] w-full mt-4 relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={indiciosData} cx="50%" cy="50%" innerRadius={60} outerRadius={85} paddingAngle={5} dataKey="value" stroke="none" labelLine={false}>
                  {indiciosData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} className="hover:opacity-80 transition-opacity cursor-pointer" />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-4 relative z-10">
             {indiciosData.map((entry: any) => (
               <div key={entry.name} className="flex items-center gap-1.5">
                 <div className="w-2 h-2 rounded-full shadow-sm" style={{ backgroundColor: entry.fill }} />
                 <span className="text-[9px] font-bold text-text-main uppercase tracking-widest">{entry.name}</span>
               </div>
             ))}
          </div>
          <div className="absolute inset-0 bg-gradient-to-t from-bg-card via-transparent to-transparent z-0" />
        </div>

        {/* MANTENDO OS ORIGINAIS MAS COM COPY DE MARKETING */}

        {/* Ideologia Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-500/10 rounded-xl">
                <Filter className="w-5 h-5 text-indigo-500" />
              </div>
              <div>
                <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Anatomia Ideológica</h2>
                <p className="text-[10px] text-text-muted font-bold uppercase mt-1">Perfil de interesse da rede</p>
              </div>
            </div>
          </div>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie activeIndex={activeIndex} activeShape={renderActiveShape} data={ideologia} cx="50%" cy="50%" innerRadius={70} outerRadius={95} paddingAngle={5} dataKey="value" onMouseEnter={onPieEnter} stroke="none">
                  {ideologia.map((entry: any, index: number) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Gender Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center gap-3">
            <div className="p-2 bg-pink-500/10 rounded-xl">
              <Users className="w-5 h-5 text-pink-500" />
            </div>
            <div>
              <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Segmentação (Gênero)</h2>
              <p className="text-[10px] text-text-muted font-bold uppercase mt-1">Identificação estatística</p>
            </div>
          </div>
          <div className="h-[250px] w-full mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sexo} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                <defs>
                  <linearGradient id="colorGender0" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ec4899" stopOpacity={0.8}/><stop offset="95%" stopColor="#ec4899" stopOpacity={0.2}/></linearGradient>
                  <linearGradient id="colorGender1" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0.2}/></linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={10} fontWeight="bold" />
                <YAxis hide />
                <Tooltip cursor={{ fill: '#334155', opacity: 0.05 }} content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={50} animationDuration={1500}>
                  {sexo.map((entry: any, index: number) => <Cell key={`cell-${index}`} fill={`url(#colorGender${index % 2})`} stroke={index === 0 ? '#ec4899' : '#3b82f6'} strokeWidth={1} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Party Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-xl"><BarChart3 className="w-5 h-5 text-blue-500" /></div>
            <div>
              <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Correlação Partidária</h2>
              <p className="text-[10px] text-text-muted font-bold uppercase mt-1">Interação por afinidade política</p>
            </div>
          </div>
          <div className="h-[280px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={partido} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorParty" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8}/><stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.8}/></linearGradient>
                </defs>
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} width={80} fontWeight="bold" />
                <Tooltip cursor={{ fill: '#334155', opacity: 0.05 }} content={<CustomTooltip />} />
                <Bar dataKey="value" fill="url(#colorParty)" radius={[0, 6, 6, 0]} barSize={20} animationDuration={1500}>
                  {partido.map((entry: any, index: number) => <Cell key={`cell-${index}`} fill="url(#colorParty)" />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* State Chart */}
        <div className="bg-bg-card border border-border-main rounded-3xl p-8 shadow-sm glass-card hover:shadow-md transition-shadow">
          <div className="mb-6 flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-xl"><MapPin className="w-5 h-5 text-emerald-500" /></div>
            <div>
              <h2 className="text-lg font-black text-text-main uppercase tracking-tight">Zona de Impacto Geográfico</h2>
              <p className="text-[10px] text-text-muted font-bold uppercase mt-1">Identificação da origem territorial do fluxo</p>
            </div>
          </div>
          <div className="h-[280px] w-full mt-4">
            {estado && estado.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={estado} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorState" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#10b981" stopOpacity={0.8}/><stop offset="100%" stopColor="#059669" stopOpacity={0.8}/></linearGradient>
                  </defs>
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} width={50} fontWeight="bold" />
                  <Tooltip cursor={{ fill: '#334155', opacity: 0.05 }} content={<CustomTooltip />} />
                  <Bar dataKey="value" fill="url(#colorState)" radius={[0, 6, 6, 0]} barSize={20} animationDuration={1500}>
                    {estado.map((entry: any, index: number) => <Cell key={`cell-${index}`} fill="url(#colorState)" />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center border-2 border-dashed border-border-main/50 rounded-2xl">
                <MapPin className="w-8 h-8 text-text-muted/30 mb-2" />
                <p className="text-xs text-text-muted font-bold uppercase tracking-widest">Calculando triangulação geográfica...</p>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* CTA Final (Desejo de Compra / Escassez) */}
      <div className="mt-12 bg-gradient-to-br from-bg-card to-red-900/10 p-10 rounded-3xl border border-red-500/20 glass-card relative overflow-hidden text-center flex flex-col items-center justify-center">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-red-500 to-transparent opacity-80" />
        <ShieldAlert className="w-12 h-12 text-red-500 mb-6" />
        <h2 className="text-3xl font-black text-text-main uppercase tracking-tight mb-4">
          Ataques isolados não mapeiam a rede completa
        </h2>
        <p className="text-text-muted max-w-2xl mb-8 font-medium">
          Ao solicitar o Dossiê Analítico Completo, nossa IA extrai, certifica e gera material com consolidação rigorosa de informações (Assinatura SHA-256). 
          Proteja sua reputação e mapeie clusters de atividades coordenadas.
        </p>
        <button className="bg-red-600 hover:bg-red-500 text-white font-black uppercase tracking-widest px-10 py-5 rounded-xl shadow-[0_0_30px_rgba(220,38,38,0.4)] hover:shadow-[0_0_50px_rgba(220,38,38,0.6)] transition-all duration-300 hover:-translate-y-1 flex items-center justify-center gap-3">
          <Sparkles className="w-5 h-5" /> Emitir Dossiê Analítico Agora
        </button>
      </div>

    </div>
  );
}

