"""FastAPI application entry point."""
import logging
import os
from logging.handlers import RotatingFileHandler
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
from .settings import settings

# Configure logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

# Root logger configuration
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Console handler (always enabled)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(console_handler)

# File handler (optional, if LOG_FILE_PATH is set)
if settings.log_file_path:
    try:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(settings.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"Created log directory: {log_dir}")  # Use print since logger might not be ready
        
        # Rotating file handler: max 10MB per file, keep 5 backup files
        file_handler = RotatingFileHandler(
            settings.log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        root_logger.addHandler(file_handler)
        print(f"File logging enabled: {settings.log_file_path}")  # Use print since logger might not be ready
    except Exception as e:
        # Log error but don't crash - console logging will still work
        print(f"WARNING: Failed to set up file logging to {settings.log_file_path}: {str(e)}")
        import traceback
        traceback.print_exc()

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Policy & Product Helper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine and register with routes
logger.info("Initializing RAG engine...")
logger.info(f"Configuration: LLM={settings.llm_provider}, VectorStore={settings.vector_store}, EmbeddingModel={settings.embedding_model}")
if settings.log_file_path:
    logger.info(f"Logging to file: {settings.log_file_path}")
engine = RAGEngine()
set_engine(engine)
logger.info("RAG engine initialized successfully")

# Register routes
app.get("/api/health")(get_health)
app.get("/api/metrics", response_model=MetricsResponse)(get_metrics)
app.post("/api/ingest", response_model=IngestResponse)(post_ingest)
app.post("/api/ask", response_model=AskResponse)(post_ask)
