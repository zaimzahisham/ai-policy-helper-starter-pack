"""FastAPI route handlers."""
from fastapi import HTTPException
from typing import List
from .schemas import IngestResponse, AskRequest, AskResponse, MetricsResponse, Citation, Chunk
from ..settings import settings
from ..ingest import load_documents, build_chunks_from_docs
from ..rag import RAGEngine


# Global RAG engine instance (initialized in main.py)
# Tests can override this via set_engine()
_engine: RAGEngine | None = None


def set_engine(rag_engine: RAGEngine):
    """Set the global RAG engine instance."""
    global _engine
    _engine = rag_engine


def get_engine() -> RAGEngine:
    """Get the global RAG engine instance."""
    global _engine
    if _engine is None:
        # Lazy initialization for tests
        _engine = RAGEngine()
    return _engine


def get_health():
    """Health check endpoint."""
    return {"status": "ok"}


def get_metrics() -> MetricsResponse:
    """Get system metrics."""
    engine = get_engine()
    s = engine.stats()
    return MetricsResponse(**s)


def post_ingest() -> IngestResponse:
    """Ingest documents from data directory."""
    engine = get_engine()
    try:
        docs = load_documents(settings.data_dir)
        chunks = build_chunks_from_docs(docs, settings.chunk_size, settings.chunk_overlap)
        new_docs, new_chunks = engine.ingest_chunks(chunks)
        return IngestResponse(indexed_docs=new_docs, indexed_chunks=new_chunks)
    except Exception as e:
        if isinstance(e, FileNotFoundError):
            raise HTTPException(status_code=404, detail=f"Data directory not found: {settings.data_dir}")
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")


def post_ask(req: AskRequest) -> AskResponse:
    """Ask a question and get an answer with citations."""
    engine = get_engine()
    ctx = engine.retrieve(req.query, k=req.k or 4)
    answer = engine.generate(req.query, ctx)
    citations = [Citation(title=c.get("title"), section=c.get("section")) for c in ctx]
    chunks = [Chunk(title=c.get("title"), section=c.get("section"), text=c.get("text")) for c in ctx]
    stats = engine.stats()
    # Create MetricsResponse and convert to dict, then add legacy fields
    metrics_dict = MetricsResponse(**stats).model_dump()
    metrics_dict.update({
        # Legacy fields for backward compatibility
        "retrieval_ms": stats["avg_retrieval_latency_ms"],
        "generation_ms": stats["avg_generation_latency_ms"],
    })
    return AskResponse(
        query=req.query,
        answer=answer,
        citations=citations,
        chunks=chunks,
        metrics=metrics_dict
    )

