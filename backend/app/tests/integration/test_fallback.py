import pytest
from app import rag

def test_qdrant_fallback(monkeypatch):
    class BoomClient:
        def __init__(*args, **kwargs):
            raise ConnectionError("qdrant down")

    # Patch QdrantClient where it's imported in stores.py
    monkeypatch.setattr("app.rag.stores.QdrantClient", BoomClient)
    engine = rag.RAGEngine()
    assert engine.store.__class__.__name__ == "InMemoryStore"

    # Optional: verify ingest still works with fallback
    docs = [{"title": "Doc", "section": "Body", "text": "hello world"}]
    from app.ingest import build_chunks_from_docs
    chunks = build_chunks_from_docs(docs, chunk_size=5, overlap=0)
    engine.ingest_chunks(chunks)  # should not raise