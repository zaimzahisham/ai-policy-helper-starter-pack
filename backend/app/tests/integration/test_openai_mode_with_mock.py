import pytest
from app import rag

def test_openai_mode_with_mock(monkeypatch, client):
    class FakeOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
        def generate(self, query, contexts):
            return "mocked openai answer"

    monkeypatch.setattr(rag, "OpenAILLM", lambda api_key: FakeOpenAI(api_key))
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    from app.settings import settings
    settings.llm_provider = "openai"
    settings.openai_api_key = "dummy"

    # Need a fresh engine after env changes
    rag_engine = rag.RAGEngine()
    # optionally swap main.engine = rag_engine if tests use global
    from app import main
    main.engine = rag_engine

    client.post("/api/ingest")
    resp = client.post("/api/ask", json={"query": "hello?"})
    assert resp.status_code == 200
    assert "mocked openai answer" in resp.json()["answer"]
    assert len(resp.json()["citations"]) > 0