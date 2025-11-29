"""API request/response schemas (Pydantic models)."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class IngestResponse(BaseModel):
    """Response for document ingestion endpoint."""
    indexed_docs: int
    indexed_chunks: int


class AskRequest(BaseModel):
    """Request for asking questions."""
    query: str
    k: int | None = 4


class Citation(BaseModel):
    """Citation reference to a document section."""
    title: str
    section: str | None = None


class Chunk(BaseModel):
    """Retrieved chunk with metadata."""
    title: str
    section: str | None = None
    text: str


class AskResponse(BaseModel):
    """Response for ask endpoint."""
    query: str
    answer: str
    citations: List[Citation]
    chunks: List[Chunk]
    metrics: Dict[str, Any]


class MetricsResponse(BaseModel):
    """Response for metrics endpoint."""
    total_docs: int
    total_chunks: int
    ask_count: int
    fallback_used: bool
    avg_retrieval_latency_ms: float
    avg_generation_latency_ms: float
    embedding_model: str
    llm_model: str

