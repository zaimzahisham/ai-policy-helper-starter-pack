"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .rag import RAGEngine
from .api.routes import (
    set_engine,
    get_health,
    get_metrics,
    post_ingest,
    post_ask,
)
from .api.schemas import IngestResponse, AskRequest, AskResponse, MetricsResponse

app = FastAPI(title="AI Policy & Product Helper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine and register with routes
engine = RAGEngine()
set_engine(engine)

# Register routes
app.get("/api/health")(get_health)
app.get("/api/metrics", response_model=MetricsResponse)(get_metrics)
app.post("/api/ingest", response_model=IngestResponse)(post_ingest)
app.post("/api/ask", response_model=AskResponse)(post_ask)
