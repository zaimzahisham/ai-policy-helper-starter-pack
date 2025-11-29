import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).resolve().parents[2]))
from app import main
from app.api.routes import set_engine
from app.rag import RAGEngine

@pytest.fixture(autouse=True)
def reset_engine():
    """Reset engine before each test to ensure clean state."""
    engine = RAGEngine()
    set_engine(engine)
    yield

@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)
