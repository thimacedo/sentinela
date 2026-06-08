/**
 * PASA v50.1 - API Gateway Client
 * Centraliza as chamadas para o backend FastAPI com suporte a fallback e ambiente local.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchApi(path: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${path}`;
  
  const response = await fetch(url, {
    cache: 'no-store', // Avoid Next.js or browser caching
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function postCommand(command: 'PAUSE' | 'RESUME') {
  return fetchApi('/api/v1/command', {
    method: 'POST',
    body: JSON.stringify({ command }),
  });
}

// ─── DASHBOARD ENDPOINTS ───

export async function getSummaryStats() {
  return fetchApi('/api/v1/summary');
}

export async function getTargets(limit = 50) {
  return fetchApi(`/api/v1/targets?limit=${limit}`);
}

export async function getActiveAlerts(limit = 20) {
  return fetchApi(`/api/v1/alerts/active?limit=${limit}`);
}

export async function getDossiers(candidatoId?: string) {
  const params = candidatoId ? `?candidato_id=${candidatoId}` : '';
  return fetchApi(`/api/v1/dossiers${params}`);
}

export async function getTemporalSeries() {
  return fetchApi('/api/v1/analytics/temporal-series');
}

export async function getNetworks() {
  return fetchApi('/api/v1/networks');
}
