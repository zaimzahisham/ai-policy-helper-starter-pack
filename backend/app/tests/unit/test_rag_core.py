"""Unit tests for RAG engine core functionality."""
from app.rag import RAGEngine


def test_rag_engine_loads_agent_guide():
    """
    RAGEngine should load Internal_SOP_Agent_Guide.md (if present) as agent_guide
    so it can be used as system instructions for all LLMs.
    """
    engine = RAGEngine()
    # We don't assert exact contents, just that it's a string and that the key guidance
    # phrase appears when the file is present.
    assert hasattr(engine, "agent_guide")
    assert isinstance(engine.agent_guide, str)
    # This phrase comes from Internal_SOP_Agent_Guide.md
    # If the file is missing, agent_guide may be empty, which is acceptable.
    if engine.agent_guide:
        assert "Never invent facts" in engine.agent_guide

