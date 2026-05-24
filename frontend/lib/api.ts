/**
 * PASA v50.1 - API Gateway Client
 * Centraliza as chamadas para o backend FastAPI com suporte a fallback e ambiente local.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchApi(path: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${path}`;
  
  const response = await fetch(url, {
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
