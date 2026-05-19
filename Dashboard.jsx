import { useState, useEffect, useCallback } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from "recharts";

/**
 * SENTINELA DEMOCRÁTICA — DASHBOARD WAR ROOM (PASA v50.0)
 * 
 * Implementações:
 * - Fix #4: Template literals corrigidos e robustez no parser JSON do Claude.
 * - Fix #2: Paralelização de chamadas via Promise.all().
 * - Fix #3: Agregação SQL otimizada para reduzir payload e latência.
 */

const CATEGORY_COLORS = {
  "Xenofobia Regional": "#f97316",
  "Racismo Religioso": "#a855f7",
  "Misoginia Política": "#ec4899",
  "Ataque Institucional": "#3b82f6",
  "Rigor Criminal": "#ef4444",
  "Ameaça Direta": "#dc2626",
  "Outros": "#6b7280",
};

const CAT_COLOR = (cat) => CATEGORY_COLORS[cat] || "#6b7280";
const fmt = (n) => (n ?? 0).toLocaleString("pt-BR");
const pct = (a, b) => b ? ((a / b) * 100).toFixed(1) + "%" : "0%";

async function callMCP(projectId, sql) {
  // NOTA: Em produção, mover para um Proxy Backend (Supabase Edge Function)
  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY; 
  
  if (!apiKey) {
    throw new Error("VITE_ANTHROPIC_API_KEY não configurada.");
  }

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": "mcp-client-2025-04-04"
    },
    body: JSON.stringify({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 8000,
      mcp_servers: [{ type: "url", url: "https://mcp.supabase.com/mcp", name: "supabase" }],
      messages: [{
        role: "user",
        content: `Use the Supabase MCP tool to execute this SQL on project ${projectId} and return ONLY the raw JSON array result, no explanation, no markdown fences:\n\n${sql}`
      }]
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(`Erro na API Anthropic (${res.status}): ${errorData.error?.message || res.statusText}`);
  }

  const data = await res.json();
  const text = data.content?.filter(b => b.type === "text").map(b => b.text).join("") || "[]";
  
  // Parser Robusto: Procura o primeiro bloco de array ou objeto JSON
  try {
    const match = text.match(/\[[\s\S]*\]|\{[\s\S]*\}/);
    if (!match) throw new Error("O Claude não retornou um formato JSON válido.");
    return JSON.parse(match[0]);
  } catch (err) {
    console.error("Falha no parse do Claude:", text);
    throw new Error("Erro ao interpretar dados do banco.");
  }
}

// Sub-componentes UI
function KPI({ label, value, sub, color = "#22d3ee" }) {
  return (
    <div className="rounded-xl p-4 transition-all hover:border-slate-600" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
      <p className="text-xs uppercase tracking-widest mb-1 font-semibold" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-3xl font-bold" style={{ color }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: "#475569" }}>{sub}</p>}
    </div>
  );
}

function SectionTitle({ children }) {
  return <h2 className="text-sm font-bold uppercase tracking-widest mb-4 flex items-center gap-2" style={{ color: "#38bdf8" }}>{children}</h2>;
}

function Badge({ cat }) {
  return (
    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-tighter" style={{ background: CAT_COLOR(cat) + "33", color: CAT_COLOR(cat), border: `1px solid ${CAT_COLOR(cat)}44` }}>
      {cat || "—"}
    </span>
  );
}

export function ConfigScreen({ onConnect }) {
  const [projectId, setProjectId] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function handle() {
    if (!projectId.trim()) return;
    setErr(""); setLoading(true);
    try {
      // Teste de conexão minimalista
      const result = await callMCP(projectId.trim(), "SELECT current_database() as db;");
      if (!Array.isArray(result)) throw new Error("Resposta de conexão inválida.");
      onConnect(projectId.trim());
    } catch (e) {
      setErr(e.message);
    } finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#020817" }}>
      <div className="rounded-2xl p-8 w-full max-w-md shadow-2xl" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
        <div className="flex items-center gap-3 mb-8">
          <span className="text-4xl">🛡️</span>
          <div>
            <p className="text-lg font-black text-white uppercase tracking-tighter">Sentinela Democrática</p>
            <p className="text-[10px] font-mono" style={{ color: "#475569" }}>WAR ROOM — PASA v50.0 · DIAMOND</p>
          </div>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="text-[10px] font-bold mb-1.5 block uppercase tracking-widest" style={{ color: "#64748b" }}>Supabase Project Reference</label>
            <input 
              value={projectId} 
              onChange={e => setProjectId(e.target.value)}
              placeholder="Ex: vhamejkldzxbeibqeqpk"
              className="w-full rounded-lg px-4 py-3 text-sm text-white outline-none transition-all focus:ring-2 focus:ring-sky-500"
              style={{ background: "#1e293b", border: "1px solid #334155" }} 
            />
          </div>
          
          {err && <div className="p-3 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400 font-mono">{err}</div>}
          
          <button 
            onClick={handle} 
            disabled={loading || !projectId}
            className="w-full py-3 rounded-lg font-bold text-sm transition-all active:scale-[0.98]"
            style={{ 
              background: "linear-gradient(135deg,#0ea5e9,#6366f1)", 
              color: "#fff", 
              opacity: loading || !projectId ? 0.5 : 1,
              boxShadow: "0 4px 15px rgba(14, 165, 233, 0.3)"
            }}>
            {loading ? "Estabelecendo Túnel MCP..." : "Acessar Centro de Comando"}
          </button>
        </div>

        <p className="text-[9px] mt-6 text-center leading-relaxed" style={{ color: "#334155" }}>
          PROTOCOL PASA V50 REQUIRES ANTHROPIC_API_KEY CONFIGURED.<br/>
          ALL QUERIES ARE AUDITED VIA CLAUDE SONNET 3.5.
        </p>
      </div>
    </div>
  );
}

export default function Dashboard({ projectId, onLogout }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [err, setErr] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setErr("");
    try {
      setLoadingMsg("Sincronizando Inteligência...");

      // FIX #2 & #3: Paralelização e Agregação SQL
      const [kpis, timeline, categorias, candidatos, fila, dossies, recentes] = await Promise.all([
        // KPI Principal
        callMCP(projectId, `
          SELECT 
            count(*) as total,
            count(*) FILTER (WHERE is_hate) as hate,
            COALESCE(avg(confianca_ia), 0) as avg_ccf,
            count(*) FILTER (WHERE needs_review) as needs_review,
            count(*) FILTER (WHERE audit_discrepancy) as discrepancy
          FROM comentarios;
        `),
        // Evolução 14 dias
        callMCP(projectId, `
          SELECT 
            data_coleta::date as date,
            count(*) as total,
            count(*) FILTER (WHERE is_hate) as hate
          FROM comentarios 
          WHERE data_coleta >= now() - interval '14 days'
          GROUP BY 1 ORDER BY 1;
        `),
        // Categorias de Hostilidade
        callMCP(projectId, `
          SELECT categoria_ia as name, count(*) as value
          FROM comentarios WHERE is_hate = true AND categoria_ia IS NOT NULL
          GROUP BY 1 ORDER BY 2 DESC;
        `),
        // Candidatos Top
        callMCP(projectId, `
          SELECT id, username, nome_completo, cargo, estado, 
                 comentarios_totais_count, comentarios_odio_count, shadowban_suspect
          FROM candidatos ORDER BY comentarios_odio_count DESC NULLS LAST LIMIT 10;
        `),
        // Fila Status
        callMCP(projectId, `SELECT status, count(*) as count FROM fila_coleta GROUP BY 1;`),
        // Dossiês
        callMCP(projectId, `
          SELECT id, candidato_id, data_geracao, total_comentarios, total_hate, versao_pasa
          FROM dossies ORDER BY data_geracao DESC LIMIT 5;
        `),
        // Amostra Recente para Alertas
        callMCP(projectId, `
          SELECT id, autor_username, texto_bruto, categoria_ia, confianca_ia, direcao_odio, needs_review, audit_discrepancy
          FROM comentarios WHERE is_hate = true ORDER BY data_coleta DESC LIMIT 30;
        `)
      ]);

      setData({ 
        kpis: kpis[0], 
        timeline, 
        categorias, 
        candidatos, 
        fila, 
        dossies, 
        recentes 
      });
      setLastUpdate(new Date());
    } catch (e) { 
      setErr(e.message); 
    } finally { 
      setLoading(false); 
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#020817" }}>
      <div className="text-center animate-pulse">
        <div className="text-5xl mb-4">🛡️</div>
        <p className="text-sm font-bold tracking-[0.2em] text-sky-400 uppercase">{loadingMsg}</p>
        <p className="text-[10px] mt-2 font-mono" style={{ color: "#334155" }}>ESTABLISHING SECURE PGMQ LINK...</p>
      </div>
    </div>
  );

  if (err) return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#020817" }}>
      <div className="text-center max-w-sm p-6 rounded-xl border border-red-500/20 bg-red-500/5">
        <div className="text-red-500 font-bold mb-2">CRITICAL SYSTEM ERROR</div>
        <p className="text-red-400/80 mb-6 text-xs font-mono">{err}</p>
        <div className="flex gap-2">
          <button onClick={load} className="flex-1 px-4 py-2 rounded text-xs font-bold bg-slate-800 text-white hover:bg-slate-700">RETRY SYNC</button>
          <button onClick={onLogout} className="px-4 py-2 rounded text-xs font-bold bg-slate-900 text-slate-500 hover:text-slate-300">RECONFIGURE</button>
        </div>
      </div>
    </div>
  );

  const { kpis, timeline, categorias, candidatos, fila, dossies, recentes } = data;

  return (
    <div className="min-h-screen p-4 md:p-8" style={{ background: "#020817", color: "#e2e8f0" }}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-800/50">
        <div className="flex items-center gap-4">
          <span className="text-4xl drop-shadow-[0_0_10px_rgba(56,189,248,0.5)]">🛡️</span>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Sentinela Democrática</h1>
            <p className="text-[10px] font-mono tracking-widest" style={{ color: "#475569" }}>
              STRATEGIC COMMAND · PASA v50.0 · {lastUpdate?.toLocaleTimeString("pt-BR")}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-lg border border-slate-800">
          <div className="flex items-center gap-2 text-[10px] px-3 py-1.5 rounded-md bg-green-500/10 text-green-400 font-bold border border-green-500/20">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /> SYSTEM LINK ACTIVE
          </div>
          <button onClick={load} className="text-xs p-1.5 rounded-md hover:bg-slate-800 text-slate-400 transition-colors" title="Recarregar">↻</button>
          <button onClick={onLogout} className="text-[10px] font-bold px-3 py-1.5 rounded-md bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-all border border-red-500/10">TERMINATE</button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KPI label="Total Coletado" value={fmt(kpis.total)} sub="Base Histórica" />
        <KPI label="Discurso de Ódio" value={fmt(kpis.hate)} sub={`${pct(kpis.hate, kpis.total)} de incidência`} color="#f87171" />
        <KPI label="Score CCF Médio" value={(kpis.avg_ccf * 100).toFixed(1) + "%"} sub="Confiança de Classificação" color="#a78bfa" />
        <KPI label="Audit Discrepancy" value={fmt(kpis.discrepancy)} sub="Alertas de Auditoria" color="#f97316" />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KPI label="Requer Revisão" value={fmt(kpis.needs_review)} color="#fbbf24" />
        <KPI label="Fila de Coleta" value={fmt(fila.reduce((s,f) => s + f.count, 0))} sub={fila.map(f => `${f.status}:${f.count}`).join(" · ")} color="#38bdf8" />
        <KPI label="Alvos Monitorados" value={fmt(candidatos.length)} sub={`${candidatos.filter(c => c.shadowban_suspect).length} suspeitas shadowban`} color="#34d399" />
        <KPI label="Dossiês Gerados" value={fmt(dossies.length)} sub={dossies[0] ? `Último: ${dossies[0].data_geracao?.slice(0, 10)}` : "—"} color="#e879f9" />
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <div className="rounded-2xl p-6" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>📈 Evolução Temporal (14 dias)</SectionTitle>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeline}>
              <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#475569", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip 
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "8px", fontSize: 11 }}
                itemStyle={{ padding: 0 }}
              />
              <Line type="monotone" dataKey="total" stroke="#38bdf8" dot={false} strokeWidth={3} name="Total" />
              <Line type="monotone" dataKey="hate" stroke="#f87171" dot={false} strokeWidth={3} name="Ódio" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl p-6" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>📊 Hostilidade por Categoria</SectionTitle>
          {categorias.length === 0 ? <p className="text-xs italic text-slate-500">Aguardando dados de classificação...</p> : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={categorias} layout="vertical">
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} width={140} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 11 }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                  {categorias.map((e, i) => <Cell key={i} fill={CAT_COLOR(e.name)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Candidates Table */}
        <div className="lg:col-span-2 rounded-2xl p-6" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>🏆 Ranking de Hostilidade por Alvo</SectionTitle>
          <div className="space-y-4">
            {candidatos.map((c, i) => (
              <div key={c.id} className="group flex items-center gap-4 text-xs p-3 rounded-xl hover:bg-slate-800/50 transition-all border border-transparent hover:border-slate-700/50">
                <span className="font-black text-slate-700 group-hover:text-slate-500 w-6">{(i + 1).toString().padStart(2, '0')}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white truncate">{c.nome_completo || c.username}</span>
                    <span className="text-[10px] text-slate-500 font-mono">@{c.username}</span>
                    {c.shadowban_suspect && <span className="text-yellow-500 text-[10px]" title="Suspeita de Shadowban">⚠️</span>}
                  </div>
                  <div className="text-[9px] text-slate-500 mt-0.5 uppercase tracking-tighter">
                    {c.cargo} · {c.estado}
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center justify-end gap-2 mb-1">
                    <span className="text-red-400 font-black text-sm">{fmt(c.comentarios_odio_count)}</span>
                    <span className="text-slate-600 font-mono">/ {fmt(c.comentarios_totais_count)}</span>
                  </div>
                  <div className="w-32 h-1.5 rounded-full bg-slate-900 border border-slate-800 overflow-hidden">
                    <div 
                      className="h-full rounded-full transition-all duration-1000" 
                      style={{ 
                        width: pct(c.comentarios_odio_count, c.comentarios_totais_count), 
                        background: "linear-gradient(90deg, #ef4444, #dc2626)" 
                      }} 
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        <div className="rounded-2xl p-6" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>🚨 Alertas de Monitoramento</SectionTitle>
          <div className="space-y-3 overflow-y-auto pr-2" style={{ maxHeight: '600px' }}>
            {recentes.map((c) => (
              <div key={c.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800/50 hover:border-slate-700 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-sky-500 text-[10px]">@{c.autor_username}</span>
                  <Badge cat={c.categoria_ia} />
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed mb-3 line-clamp-3 italic">"{c.texto_bruto}"</p>
                <div className="flex items-center justify-between pt-2 border-t border-slate-900">
                  <div className="flex gap-1">
                    {c.needs_review && <span className="text-yellow-500 text-[10px]">🔍</span>}
                    {c.audit_discrepancy && <span className="text-orange-500 text-[10px]">⚡</span>}
                  </div>
                  <span className="text-[10px] font-black" style={{ color: c.confianca_ia > 0.8 ? "#f87171" : "#4ade80" }}>
                    CCF: {(c.confianca_ia * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Dossiês Footer */}
      {dossies.length > 0 && (
        <div className="rounded-2xl p-6" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>📁 Inteligência Gerada (Dossiês)</SectionTitle>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {dossies.map(d => (
              <div key={d.id} className="p-3 rounded-lg bg-slate-950 border border-slate-800 hover:bg-slate-900 transition-colors cursor-pointer group">
                <p className="text-[10px] font-bold text-slate-500 mb-1">{d.data_geracao?.slice(0, 10)}</p>
                <p className="text-xs font-black text-white group-hover:text-sky-400 transition-colors">ID: {d.candidato_id?.slice(0, 8)}</p>
                <div className="mt-2 flex justify-between items-end">
                   <span className="text-[9px] font-mono text-slate-500">{d.versao_pasa}</span>
                   <span className="text-[10px] font-bold text-red-500">{fmt(d.total_hate)} HITS</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-center text-[9px] mt-12 font-mono uppercase tracking-[0.3em] text-slate-700">
        Sentinela Democrática Strategic Interface · Secure Encryption Enabled · Diamond PASA Engine
      </p>
    </div>
  );
}
