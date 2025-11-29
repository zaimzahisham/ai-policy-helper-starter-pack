"""FastAPI route handlers."""
import logging
from fastapi import HTTPException
from typing import List
from .schemas import IngestResponse, AskRequest, AskResponse, MetricsResponse, Citation, Chunk
from ..settings import settings
from ..ingest import load_documents, build_chunks_from_docs
from ..rag import RAGEngine

logger = logging.getLogger(__name__)


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
    try:
        logger.info("GET /api/metrics - Fetching system metrics")
        engine = get_engine()
        s = engine.stats()
        logger.info(f"Metrics retrieved: {s.get('total_docs')} docs, {s.get('total_chunks')} chunks, {s.get('ask_count')} asks")
        return MetricsResponse(**s)
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


def post_ingest() -> IngestResponse:
    """Ingest documents from data directory."""
    logger.info(f"POST /api/ingest - Starting ingestion from {settings.data_dir}")
    engine = get_engine()
    try:
        docs = load_documents(settings.data_dir)
        logger.info(f"Loaded {len(docs)} document sections")
        chunks = build_chunks_from_docs(docs, settings.chunk_size, settings.chunk_overlap)
        logger.info(f"Built {len(chunks)} chunks from documents")
        new_docs, new_chunks = engine.ingest_chunks(chunks)
        logger.info(f"Ingestion complete: {new_docs} new docs, {new_chunks} new chunks indexed")
        return IngestResponse(indexed_docs=new_docs, indexed_chunks=new_chunks)
    except FileNotFoundError as e:
        logger.error(f"Data directory not found: {settings.data_dir}")
        raise HTTPException(status_code=404, detail=f"Data directory not found: {settings.data_dir}")
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting documents: {str(e)}")


def post_ask(req: AskRequest) -> AskResponse:
    """Ask a question and get an answer with citations."""
    query_preview = req.query[:50] + "..." if len(req.query) > 50 else req.query
    logger.info(f"POST /api/ask - Query: '{query_preview}' (k={req.k or 4})")
    engine = get_engine()
    try:
        ctx = engine.retrieve(req.query, k=req.k or 4)
        logger.info(f"Retrieved {len(ctx)} chunks for query")
        answer = engine.generate(req.query, ctx)
        logger.info(f"Generated answer (length: {len(answer)} chars)")
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
        logger.info(f"Query completed: {len(citations)} citations, retrieval={stats['avg_retrieval_latency_ms']:.2f}ms, generation={stats['avg_generation_latency_ms']:.2f}ms")
        return AskResponse(
            query=req.query,
            answer=answer,
            citations=citations,
            chunks=chunks,
            metrics=metrics_dict
        )
    except Exception as e:
        logger.error(f"Error processing query '{query_preview}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

