import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": Deno.env.get("ALLOWED_ORIGIN") ?? "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const ALLOWED_PROJECTS = Deno.env.get("ALLOWED_PROJECT_IDS")?.split(",") ?? [];

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  const authHeader = req.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) {
    return json({ error: "Unauthorized" }, 401);
  }

  let body: { projectId: string; sql: string };
  try {
    body = await req.json();
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }

  const { projectId, sql } = body;

  if (!projectId || !sql) {
    return json({ error: "projectId e sql são obrigatórios" }, 400);
  }

  const normalized = sql.trim().toUpperCase();
  if (!normalized.startsWith("SELECT")) {
    return json({ error: "Apenas queries SELECT são permitidas" }, 403);
  }

  if (ALLOWED_PROJECTS.length > 0 && !ALLOWED_PROJECTS.includes(projectId)) {
    return json({ error: "Project ID não autorizado" }, 403);
  }

  const apiKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!apiKey) {
    return json({ error: "Configuração de servidor inválida" }, 500);
  }

  try {
    const anthropicRes = await fetch(ANTHROPIC_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "mcp-client-2025-04-04",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 8000,
        mcp_servers: [{
          type: "url",
          url: "https://mcp.supabase.com/mcp",
          name: "supabase",
        }],
        messages: [{
          role: "user",
          content: `Use the Supabase MCP tool to execute this SQL on project ${projectId} and return ONLY the raw JSON array result, no explanation, no markdown:\n\n${sql}`,
        }],
      }),
    });

    if (!anthropicRes.ok) {
      const errText = await anthropicRes.text();
      console.error("Anthropic error:", errText);
      return json({ error: `Anthropic API error: ${anthropicRes.status}` }, 502);
    }

    const data = await anthropicRes.json();

    const text = data.content
      ?.filter((b: { type: string }) => b.type === "text")
      .map((b: { text: string }) => b.text)
      .join("") ?? "[]";

    const match = text.match(/(\[[\s\S]*\]|\{[\s\S]*\})/);
    const result = match ? JSON.parse(match[0]) : [];

    return json({ result }, 200);

  } catch (e) {
    console.error("Proxy error:", e);
    return json({ error: "Erro interno no proxy" }, 500);
  }
});

function json(data: unknown, status: number): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}