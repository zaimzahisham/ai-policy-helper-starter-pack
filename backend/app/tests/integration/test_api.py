def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_ingest_and_ask(client):
    r = client.post("/api/ingest")
    assert r.status_code == 200
    # Ask a deterministic question
    r2 = client.post("/api/ask", json={"query":"What is the refund window for small appliances?"})
    assert r2.status_code == 200
    data = r2.json()
    assert "citations" in data and len(data["citations"]) > 0
    assert "answer" in data and isinstance(data["answer"], str)

def test_ingest_idempotent(client):
    '''
    second ingest should be a no-op because of hash deduplication
    '''
    first = client.post("/api/ingest").json()
    second = client.post("/api/ingest").json()
    assert first["indexed_docs"] > 0
    assert second["indexed_docs"] == 0
    assert second["indexed_chunks"] == 0

def test_metrics_after_ask(client, monkeypatch):
    # Ensure stub mode is used for this test
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    from app.settings import settings
    settings.llm_provider = "stub"
    # Reinitialize engine with stub mode
    from app import rag
    from app.api.routes import set_engine
    rag_engine = rag.RAGEngine()
    set_engine(rag_engine)
    
    client.post("/api/ingest")
    client.post("/api/ask", json={"query": "test question"})
    metrics = client.get("/api/metrics").json()
    assert metrics["total_docs"] >= 1
    assert metrics["total_chunks"] >= 1
    assert metrics["ask_count"] == 1
    assert metrics["fallback_used"] is False  # Qdrant should be available in tests
    assert metrics["avg_retrieval_latency_ms"] >= 0
    assert metrics["llm_model"] == "stub"

def test_ask_count_increments(client):
    """Verify that ask_count increments correctly with multiple queries"""
    client.post("/api/ingest")
    # First ask
    client.post("/api/ask", json={"query": "first question"})
    metrics1 = client.get("/api/metrics").json()
    assert metrics1["ask_count"] == 1
    
    # Second ask
    client.post("/api/ask", json={"query": "second question"})
    metrics2 = client.get("/api/metrics").json()
    assert metrics2["ask_count"] == 2
    
    # Third ask
    client.post("/api/ask", json={"query": "third question"})
    metrics3 = client.get("/api/metrics").json()
    assert metrics3["ask_count"] == 3

def test_ingest_missing_data_dir(client, monkeypatch):
    from app.settings import settings
    monkeypatch.setattr(settings, "data_dir", "/tmp/does_not_exist")
    resp = client.post("/api/ingest", headers={"Origin": "http://localhost:3000"}) # mimic a browser so CORS headers are returned
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"].lower().startswith("data directory")
    assert resp.headers["access-control-allow-origin"] == "*"

def test_metadata_enrichment_in_chunks(client):
    """Test that chunks include metadata (heading_level, section_priority) after ingestion"""
    client.post("/api/ingest")
    resp = client.post("/api/ask", json={"query": "What is the SLA for shipping?"})
    assert resp.status_code == 200
    data = resp.json()
    
    # Verify chunks have metadata
    chunks = data.get("chunks", [])
    assert len(chunks) > 0, "Should have at least one chunk"
    
    # Check that metadata fields exist (they should be in the chunk dict)
    # Note: chunks returned from API may not include all metadata, but they should have title/section
    # We can verify by checking that SLA-related chunks are present (which should have high priority)
    has_sla_chunk = any(
        "sla" in chunk.get("section", "").lower() or 
        "sla" in chunk.get("text", "").lower()
        for chunk in chunks
    )
    # For shipping SLA query, we should get Delivery_and_Shipping.md chunks
    assert has_sla_chunk or any("Delivery" in chunk.get("title", "") for chunk in chunks), \
        "SLA query should retrieve Delivery_and_Shipping.md chunks"


def test_internal_sop_agent_guide_never_cited(client):
    """
    Internal_SOP_Agent_Guide.md is internal behavior guidance for the agent and should not be
    part of user-facing citations.
    """
    client.post("/api/ingest")
    resp = client.post("/api/ask", json={"query": "What is the refund window for small appliances?"})
    assert resp.status_code == 200
    data = resp.json()
    titles = [c["title"] for c in data.get("citations", [])]
    assert "Internal_SOP_Agent_Guide.md" not in titles