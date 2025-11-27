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

def test_metrics_after_ask(client):
    client.post("/api/ingest")
    client.post("/api/ask", json={"query": "test question"})
    metrics = client.get("/api/metrics").json()
    assert metrics["total_docs"] >= 1
    assert metrics["total_chunks"] >= 1
    assert metrics["avg_retrieval_latency_ms"] >= 0
    assert metrics["llm_model"] == "stub"