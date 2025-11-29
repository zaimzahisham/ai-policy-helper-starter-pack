/**API request/response types matching backend app/api/schemas.py.*/

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
  // Matches backend/app/api/schemas.py MetricsResponse exactly
  total_docs: number;
  total_chunks: number;
  ask_count: number;
  fallback_used: boolean;
  avg_retrieval_latency_ms: number;
  avg_generation_latency_ms: number;
  embedding_model: string;
  llm_model: string;
}

