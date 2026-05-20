import { useState, useEffect, useCallback } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from "recharts";

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

// ── Proxy Config ──────────────────────────────────────────────────────────────
const PROXY_URL = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/mcp-proxy`;
const ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

async function callProxy(projectId, action) {
  const res = await fetch(PROXY_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${ANON_KEY}`,
    },
    body: JSON.stringify({ projectId, action }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`[${action}] Proxy error ${res.status}: ${text}`);
  }

  const { result, error } = await res.json();
  if (error) throw new Error(`[${action}] ${error}`);
  return result ?? [];
}

// ── Components ────────────────────────────────────────────────────────────────
function KPI({ label, value, sub, color = "#22d3ee" }) {
  return (
    <div className="rounded-xl p-4" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
      <p className="text-xs uppercase tracking-widest mb-1" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-3xl font-bold" style={{ color }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: "#475569" }}>{sub}</p>}
    </div>
  );
}

function SectionTitle({ children }) {
  return <h2 className="text-sm font-semibold uppercase tracking-widest mb-3" style={{ color: "#38bdf8" }}>{children}</h2>;
}

function Badge({ cat }) {
  return (
    <span className="px-2 py-0.5 rounded text-xs font-semibold" style={{ background: CAT_COLOR(cat) + "33", color: CAT_COLOR(cat) }}>
      {cat || "—"}
    </span>
  );
}

// ── Config Screen ─────────────────────────────────────────────────────────────
function ConfigScreen({ onConnect }) {
  const [projectId, setProjectId] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function handle() {
    setErr("");
    setLoading(true);
    try {
      // Teste de conectividade com action simples
      await callProxy(projectId.trim(), "get_kpis");
      onConnect(projectId.trim());
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#020817" }}>
      <div className="rounded-2xl p-8 w-full max-w-md" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
        <div className="flex items-center gap-2 mb-6">
          <span className="text-2xl">🛡️</span>
          <div>
            <p className="font-bold text-white">Sentinela Democrática</p>
            <p className="text-xs" style={{ color: "#475569" }}>War Room — PASA v50.1 · Hardened Proxy</p>
          </div>
        </div>
        <p className="text-sm mb-4" style={{ color: "#94a3b8" }}>
          Informe o <strong className="text-white">Project ID</strong> do seu projeto Supabase.<br />
          <span className="text-xs" style={{ color: "#475569" }}>Encontre em: Supabase Dashboard → Settings → General → Reference ID</span>
        </p>
        <div>
          <label className="text-xs mb-1 block" style={{ color: "#64748b" }}>PROJECT REFERENCE ID</label>
          <input
            value={projectId}
            onChange={e => setProjectId(e.target.value)}
            placeholder="vhamejkldzxbeibqeqpk"
            className="w-full rounded-lg px-3 py-2 text-sm text-white outline-none"
            style={{ background: "#1e293b", border: "1px solid #334155" }}
          />
        </div>
        {err && <p className="text-xs mt-3 text-red-400">{err}</p>}
        <button
          onClick={handle}
          disabled={loading || !projectId}
          className="mt-5 w-full py-2 rounded-lg font-semibold text-sm"
          style={{ background: "linear-gradient(135deg,#0ea5e9,#6366f1)", color: "#fff", opacity: loading || !projectId ? 0.5 : 1 }}
        >
          {loading ? "Conectando via Hardened Proxy..." : "Conectar ao War Room"}
        </button>
        <p className="text-xs mt-3 text-center" style={{ color: "#334155" }}>
          Conexão via Supabase MCP · Roteamento determinístico PASA v50.1
        </p>
      </div>
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function Dashboard({ projectId, onLogout }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [err, setErr] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      setLoadingMsg("Carregando dados via proxy seguro...");

      const [kpis, timeline, candidates, alerts, queue, dossiers] = await Promise.all([
        callProxy(projectId, "get_kpis"),
        callProxy(projectId, "get_timeline"),
        callProxy(projectId, "get_top_candidates"),
        callProxy(projectId, "get_alerts"),
        callProxy(projectId, "get_queue"),
        callProxy(projectId, "get_dossiers"),
      ]);

      setData({
        kpis: kpis[0] || {},
        timeline: timeline || [],
        candidates: candidates || [],
        alerts: alerts || [],
        queue: queue || [],
        dossiers: dossiers || [],
      });
      setLastUpdate(new Date());
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#020817" }}>
        <div className="text-center">
          <div className="text-4xl mb-3">⚙️</div>
          <p style={{ color: "#38bdf8" }}>{loadingMsg}</p>
          <p className="text-xs mt-2" style={{ color: "#334155" }}>Via Hardened Proxy...</p>
        </div>
      </div>
    );
  }

  if (err) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#020817" }}>
        <div className="text-center max-w-sm">
          <p className="text-red-400 mb-3 text-sm">{err}</p>
          <button onClick={load} className="px-4 py-2 rounded text-sm mr-2" style={{ background: "#1e293b", color: "#fff" }}>
            Tentar novamente
          </button>
          <button onClick={onLogout} className="px-4 py-2 rounded text-sm" style={{ background: "#1e293b", color: "#94a3b8" }}>
            Reconfigurar
          </button>
        </div>
      </div>
    );
  }

  const { kpis, timeline, candidates, alerts, queue, dossiers } = data;

  // Agregações de fila
  const queueMap = {};
  queue.forEach(q => {
    queueMap[q.status] = q.count;
  });

  // Categorias de hostilidade (derivadas dos alertas)
  const catMap = {};
  alerts.forEach(a => {
    if (a.categoria_ia) catMap[a.categoria_ia] = (catMap[a.categoria_ia] || 0) + 1;
  });
  const catData = Object.entries(catMap)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));

  // Direção do ódio
  const dirMap = {};
  alerts.forEach(a => {
    if (a.direcao_odio) dirMap[a.direcao_odio] = (dirMap[a.direcao_odio] || 0) + 1;
  });
  const dirData = Object.entries(dirMap).map(([name, value]) => ({ name, value }));

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ background: "#020817", color: "#e2e8f0" }}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🛡️</span>
          <div>
            <h1 className="text-xl font-bold text-white">Sentinela Democrática</h1>
            <p className="text-xs" style={{ color: "#475569" }}>War Room · PASA v50.1 · Hardened Edition</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full" style={{ background: "#052e16", color: "#4ade80" }}>
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" /> ONLINE
          </span>
          {lastUpdate && <span className="text-xs" style={{ color: "#475569" }}>{lastUpdate.toLocaleTimeString("pt-BR")}</span>}
          <button onClick={load} className="text-xs px-3 py-1 rounded" style={{ background: "#1e293b", color: "#94a3b8" }}>↻</button>
          <button onClick={onLogout} className="text-xs px-3 py-1 rounded" style={{ background: "#1e293b", color: "#94a3b8" }}>Sair</button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <KPI label="Comentários" value={fmt(kpis.total)} sub="Total analisados" />
        <KPI label="Discurso de Ódio" value={fmt(kpis.hate_count)} sub={pct(kpis.hate_count, kpis.total)} color="#f87171" />
        <KPI label="Score CCF Médio" value={kpis.avg_ccf ? (kpis.avg_ccf * 100).toFixed(1) + "%" : "—"} color="#a78bfa" />
        <KPI label="Candidatos" value={fmt(candidates.length)} sub={`${candidates.filter(c => c.shadowban_suspect).length} shadowban`} color="#34d399" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <KPI label="Requer Revisão" value={fmt(kpis.needs_review)} color="#fbbf24" />
        <KPI label="Discrepância" value={fmt(kpis.audit_discrepancy)} color="#f97316" />
        <KPI label="Fila de Coleta" value={fmt(queue.reduce((s, q) => s + q.count, 0))} sub={Object.entries(queueMap).map(([k, v]) => `${k}: ${v}`).join(" · ")} color="#38bdf8" />
        <KPI label="Dossiês" value={fmt(dossiers.length)} sub={dossiers[0]?.data_geracao?.slice(0, 10) || "—"} color="#e879f9" />
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <div className="rounded-xl p-4" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>📈 Evolução Temporal (14 dias)</SectionTitle>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={timeline}>
              <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 11 }} />
              <YAxis tick={{ fill: "#475569", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none", color: "#e2e8f0", fontSize: 12 }} />
              <Line type="monotone" dataKey="total" stroke="#38bdf8" dot={false} name="Total" strokeWidth={2} />
              <Line type="monotone" dataKey="hate" stroke="#f87171" dot={false} name="Ódio" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl p-4" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>📊 Categorias de Hostilidade</SectionTitle>
          {catData.length === 0 ? (
            <p className="text-xs" style={{ color: "#475569" }}>Sem dados classificados.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={catData} layout="vertical">
                <XAxis type="number" tick={{ fill: "#475569", fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} width={140} />
                <Tooltip contentStyle={{ background: "#1e293b", border: "none", color: "#e2e8f0", fontSize: 12 }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {catData.map((e, i) => <Cell key={i} fill={CAT_COLOR(e.name)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <div className="rounded-xl p-4" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>🎯 Direção do Ódio</SectionTitle>
          {dirData.length === 0 ? (
            <p className="text-xs" style={{ color: "#475569" }}>Sem dados.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={dirData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={65}
                  label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                  fontSize={10}
                >
                  {dirData.map((_, i) => <Cell key={i} fill={["#38bdf8", "#f87171", "#a78bfa", "#34d399", "#fbbf24"][i % 5]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#1e293b", border: "none", fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="md:col-span-2 rounded-xl p-4" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>🏆 Candidatos Mais Atacados</SectionTitle>
          <div className="space-y-2 overflow-y-auto" style={{ maxHeight: 200 }}>
            {candidates.length === 0 ? (
              <p className="text-xs" style={{ color: "#475569" }}>Sem dados.</p>
            ) : (
              candidates.map((c, i) => (
                <div key={c.id} className="flex items-center gap-2 text-xs">
                  <span className="font-bold w-5 text-right" style={{ color: "#475569" }}>#{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <span className="font-semibold text-white">{c.nome_completo || c.username}</span>
                    <span className="ml-1" style={{ color: "#64748b" }}>@{c.username}</span>
                    <span className="ml-2 px-1 rounded text-xs" style={{ background: "#1e293b", color: "#94a3b8" }}>
                      {c.cargo} · {c.estado}
                    </span>
                    {c.shadowban_suspect && <span className="ml-1 text-yellow-400">⚠️</span>}
                  </div>
                  <div className="text-right whitespace-nowrap">
                    <span className="text-red-400 font-bold">{fmt(c.comentarios_odio_count)}</span>
                    <span style={{ color: "#475569" }}> / {fmt(c.comentarios_totais_count)}</span>
                  </div>
                  <div className="w-20 h-1.5 rounded-full overflow-hidden flex-shrink-0" style={{ background: "#1e293b" }}>
                    <div
                      className="h-full rounded-full"
                      style={{ width: pct(c.comentarios_odio_count, c.comentarios_totais_count), background: "#f87171" }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="rounded-xl p-4 mb-6" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
        <SectionTitle>🚨 Alertas Críticos</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ color: "#475569", borderBottom: "1px solid #1e293b" }}>
                {["Autor", "Texto", "Categoria", "CCF", "Direção", "Flags"].map(h => (
                  <th key={h} className="pb-2 text-left pr-3 whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {alerts.map((c, i) => (
                <tr key={c.id} style={{ borderBottom: "1px solid #0a1628", background: i % 2 === 0 ? "#0a1628" : "transparent" }}>
                  <td className="py-1.5 pr-3 font-mono whitespace-nowrap" style={{ color: "#94a3b8" }}>@{c.autor_username || "—"}</td>
                  <td className="py-1.5 pr-3 max-w-xs truncate" style={{ color: "#e2e8f0" }} title={c.texto_bruto}>
                    {c.texto_bruto?.slice(0, 80) || "—"}
                  </td>
                  <td className="py-1.5 pr-3 whitespace-nowrap"><Badge cat={c.categoria_ia} /></td>
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    <span style={{ color: c.confianca_ia > 0.8 ? "#f87171" : c.confianca_ia > 0.5 ? "#fbbf24" : "#4ade80" }}>
                      {c.confianca_ia ? (c.confianca_ia * 100).toFixed(0) + "%" : "—"}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 whitespace-nowrap" style={{ color: "#94a3b8" }}>{c.direcao_odio || "—"}</td>
                  <td className="py-1.5 whitespace-nowrap">
                    {c.needs_review && <span className="mr-1 text-yellow-400" title="Requer revisão">🔍</span>}
                    {c.audit_discrepancy && <span className="text-orange-400" title="Discrepância">⚡</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {dossiers.length > 0 && (
        <div className="rounded-xl p-4" style={{ background: "#0f172a", border: "1px solid #1e293b" }}>
          <SectionTitle>📁 Últimos Dossiês</SectionTitle>
          <div className="space-y-2">
            {dossiers.map(d => (
              <div key={d.id} className="flex flex-wrap items-center gap-4 text-xs p-2 rounded" style={{ background: "#0a1628" }}>
                <span className="font-mono" style={{ color: "#64748b" }}>{d.data_geracao?.slice(0, 10)}</span>
                <span style={{ color: "#94a3b8" }}>
                  Candidato: <span className="text-white font-semibold">{d.candidato_id?.slice(0, 8)}…</span>
                </span>
                <span style={{ color: "#94a3b8" }}>Total: <span className="text-white">{fmt(d.total_comentarios)}</span></span>
                <span style={{ color: "#f87171" }}>Ódio: {fmt(d.total_hate)}</span>
                <span className="px-1.5 py-0.5 rounded" style={{ background: "#1e293b", color: "#38bdf8" }}>{d.versao_pasa}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-center text-xs mt-6" style={{ color: "#1e293b" }}>
        Sentinela Democrática · PASA v50.1 · Hardened Proxy
      </p>
    </div>
  );
}

export default function App() {
  const [projectId, setProjectId] = useState(null);
  if (!projectId) return <ConfigScreen onConnect={setProjectId} />;
  return <Dashboard projectId={projectId} onLogout={() => setProjectId(null)} />;
}
