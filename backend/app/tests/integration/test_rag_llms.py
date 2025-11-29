"""Integration tests for LLM providers in app/rag/llms.py."""
import pytest
from app import rag


def test_openai_llm_with_mock(monkeypatch, client):
    """Test OpenAILLM provider via mocked API call."""
    class FakeOpenAI:
        def __init__(self, api_key, agent_guide: str | None = None, required_output_format: str | None = None):
            self.api_key = api_key
            self.agent_guide = agent_guide or ""
            self.required_output_format = required_output_format or ""
        def generate(self, query, contexts):
            return "mocked openai answer"

    # Patch OpenAILLM where it's imported in core.py
    # Use string path to ensure we patch the right location
    monkeypatch.setattr("app.rag.core.OpenAILLM", lambda api_key, agent_guide=None, required_output_format=None: FakeOpenAI(api_key, agent_guide, required_output_format))
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    from app.settings import settings
    settings.llm_provider = "openai"
    settings.openai_api_key = "dummy"

    # Need a fresh engine after env changes
    rag_engine = rag.RAGEngine()
    # Set the engine in routes module
    from app.api.routes import set_engine
    set_engine(rag_engine)

    client.post("/api/ingest")
    resp = client.post("/api/ask", json={"query": "hello?"})
    assert resp.status_code == 200
    assert "mocked openai answer" in resp.json()["answer"]
    assert len(resp.json()["citations"]) > 0