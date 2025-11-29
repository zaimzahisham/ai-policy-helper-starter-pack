export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface Citation {
  title: string;
  section?: string;
}

export interface Chunk {
  title: string;
  section?: string;
  text: string;
}

export interface AskResponse {
  query: string;
  answer: string;
  citations: Citation[];
  chunks: Chunk[];
  metrics: Record<string, any>;
}

export interface IngestResponse {
  indexed_docs: number;
  indexed_chunks: number;
}

export interface MetricsResponse {
  // Matches backend/app/models.py MetricsResponse exactly
  total_docs: number;
  total_chunks: number;
  ask_count: number;
  fallback_used: boolean;
  avg_retrieval_latency_ms: number;
  avg_generation_latency_ms: number;
  embedding_model: string;
  llm_model: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // If response is not JSON, use status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function apiAsk(query: string, k: number = 4): Promise<AskResponse> {
  const r = await fetch(`${API_BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, k })
  });
  return handleResponse<AskResponse>(r);
}

export async function apiIngest(): Promise<IngestResponse> {
  const r = await fetch(`${API_BASE}/api/ingest`, { method: 'POST' });
  return handleResponse<IngestResponse>(r);
}

export async function apiMetrics(): Promise<MetricsResponse> {
  const r = await fetch(`${API_BASE}/api/metrics`);
  return handleResponse<MetricsResponse>(r);
}
