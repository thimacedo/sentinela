import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages";

// ── CORS ──────────────────────────────────────────────────────────────
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": Deno.env.get("ALLOWED_ORIGIN") ?? "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

type Action =
  | "get_kpis"
  | "get_timeline"
  | "get_top_candidates"
  | "get_alerts"
  | "get_queue"
  | "get_dossiers";

type Body = {
  projectId: string;
  action: Action;
  // hardening: não aceitamos sql do browser
  sql?: unknown;
};

// ── SQL determinístico por ação (PASA v50.1) ──────────────────────────
const ROUTES: Record<Action, string> = {
  get_kpis: `
    SELECT 
      COUNT(*) AS total, 
      COUNT(*) FILTER (WHERE is_hate) AS hate_count, 
      AVG(confianca_ia) AS avg_ccf, 
      COUNT(*) FILTER (WHERE needs_review) AS needs_review, 
      COUNT(*) FILTER (WHERE audit_discrepancy) AS audit_discrepancy 
    FROM comentarios;
  `,
  get_timeline: `
    SELECT 
      TO_CHAR(DATE(data_coleta), 'MM-DD') AS date, 
      COUNT(*) AS total, 
      COUNT(*) FILTER (WHERE is_hate) AS hate 
    FROM comentarios 
    WHERE data_coleta >= NOW() - INTERVAL '14 days' 
    GROUP BY DATE(data_coleta) 
    ORDER BY DATE(data_coleta) ASC;
  `,
  get_top_candidates: `
    SELECT 
      id, username, nome_completo, cargo, estado, partido, 
      comentarios_totais_count, comentarios_odio_count, shadowban_suspect 
    FROM candidatos 
    ORDER BY comentarios_odio_count DESC NULLS LAST 
    LIMIT 10;
  `,
  get_alerts: `
    SELECT 
      id, is_hate, categoria_ia, confianca_ia, data_coleta, autor_username, texto_bruto, direcao_odio, needs_review, audit_discrepancy 
    FROM comentarios 
    WHERE is_hate = true 
    ORDER BY data_coleta DESC 
    LIMIT 30;
  `,
  get_queue: `
    SELECT status, COUNT(*) AS count 
    FROM fila_coleta 
    GROUP BY status 
    ORDER BY status;
  `,
  get_dossiers: `
    SELECT 
      id, candidato_id, data_geracao, total_comentarios, total_hate, versao_pasa 
    FROM dossies 
    ORDER BY data_geracao DESC 
    LIMIT 5;
  `,
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

function pickJsonFromClaudeText(text: string) {
  // Extrai o primeiro array [] ou objeto {} que aparecer (robusto contra “chatter”)
  const m = text.match(/(\[[\s\S]*?\]|\{[\s\S]*?\})/);
  if (!m) return [];
  try {
    return JSON.parse(m[0]);
  } catch {
    return [];
  }
}

serve(async (req: Request) => {
  // Preflight
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  // Auth (mínimo): exige Bearer para reduzir abuso
  const auth = req.headers.get("Authorization");
  if (!auth?.startsWith("Bearer ")) {
    return json({ error: "Unauthorized" }, 401);
  }

  let body: Body;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  const { projectId, action } = body;

  // Hardening: se vier `sql` do browser, rejeita.
  if (body.sql !== undefined) {
    return json({ error: "SQL arbitrário bloqueado. Use { action }." }, 403);
  }

  if (!projectId || typeof projectId !== "string") {
    return json({ error: "projectId inválido" }, 400);
  }

  // Allowlist de projetos
  const allowedProjects = (Deno.env.get("ALLOWED_PROJECT_IDS") ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  if (allowedProjects.length > 0 && !allowedProjects.includes(projectId.trim())) {
    return json({ error: "Project ID não autorizado" }, 403);
  }

  if (!action || !(action in ROUTES)) {
    return json(
      { error: `action inválida. Permitidas: ${Object.keys(ROUTES).join(", ")}` },
      400,
    );
  }

  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!anthropicKey) {
    return json({ error: "Server misconfigured (ANTHROPIC_API_KEY)" }, 500);
  }

  const sql = ROUTES[action];

  try {
    const anthropicRes = await fetch(ANTHROPIC_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "mcp-client-2025-04-04",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 4000,
        mcp_servers: [
          {
            type: "url",
            url: "https://mcp.supabase.com/mcp",
            name: "supabase",
          },
        ],
        messages: [
          {
            role: "user",
            content: `Use the Supabase MCP tool to execute this SQL on project ${projectId} and return ONLY the raw JSON array result.\n\n${sql}`,
          },
        ],
      }),
    });

    if (!anthropicRes.ok) {
      const errText = await anthropicRes.text();
      console.error("[mcp-proxy] anthropic error:", anthropicRes.status, errText);
      return json({ error: `Anthropic API error: ${anthropicRes.status}` }, 502);
    }

    const data = await anthropicRes.json();
    const text = data.content
      ?.filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("") ?? "[]";

    const result = pickJsonFromClaudeText(text);
    return json({ result }, 200);
  } catch (e) {
    console.error("[mcp-proxy] proxy error:", e);
    return json({ error: "Erro interno no proxy" }, 500);
  }
});
