import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import os
sys.path.append(str(Path(__file__).resolve().parents[2]))
from app import main

@pytest.fixture(autouse=True)
def reset_engine():
    main.engine = main.RAGEngine()
    yield

@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)
