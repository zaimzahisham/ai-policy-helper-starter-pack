# AI Policy & Product Helper

A local-first RAG starter with **FastAPI** (backend), **Next.js** (frontend), and **Qdrant** (vector DB). Runs with one command using Docker Compose.


## Quick start

1) **Copy `.env.example` → `.env`** and edit as needed.

2) **Run everything**:
```bash
docker compose up --build
```
- Frontend: http://localhost:3000  
- Backend:  http://localhost:8000/docs  
- Qdrant:   http://localhost:6333 (UI)

3) **Ingest sample docs** (from the UI Admin tab) or:
```bash
curl -X POST http://localhost:8000/api/ingest
```

4) **Ask a question**:
```bash
curl -X POST http://localhost:8000/api/ask -H 'Content-Type: application/json' \
  -d '{"query":"What’s the shipping SLA to East Malaysia for bulky items?"}'
```

## Developer workflow

### Makefile Commands

The project includes a `Makefile` with convenient commands for common development tasks:

- **`make dev`** — Production-like build and run. Runs `docker compose up --build` for a clean, production-style verification. Useful for final testing before submission.
- **`make dev-hot`** — Hot-reload development mode. Runs `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`, bind-mounting `backend/app` and the frontend workspace so Uvicorn (`--reload`) and Next.js (`npm run dev`) hot-reload as you edit. Perfect for active development.
- **`make test`** — Run tests in container. Executes `docker compose run --rm backend pytest -q` for a reproducible test run against the last-built image.
- **`make test-hot`** — Run tests with hot-reload. Executes `docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest -q`, which bind-mounts `backend/app` during the test command so pytest sees your latest files without rebuilding. Ideal for TDD workflow.
- **`make fmt`** — Format Python code. Runs `docker compose run --rm backend black app` to format all Python code in the backend using Black formatter.

## Offline-friendly
- If you **don’t** set an API key, the backend uses a **deterministic stub LLM** and a **built-in embedding** to keep everything fully local.
- If you set `OPENAI_API_KEY` (or configure Ollama), the backend will use real models automatically.

## Project layout
```
ai-policy-helper/
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI app entry point
│  │  ├─ settings.py      # config/env
│  │  ├─ api/             # API layer
│  │  │  ├─ __init__.py
│  │  │  ├─ schemas.py    # Pydantic request/response models
│  │  │  └─ routes.py     # FastAPI route handlers
│  │  ├─ ingest/          # Document ingestion module
│  │  │  ├─ __init__.py
│  │  │  ├─ core.py       
│  │  │  ├─ helpers.py    
│  │  │  └─ utils.py      
│  │  ├─ rag/              # RAG engine module
│  │  │  ├─ __init__.py
│  │  │  ├─ core.py        # RAGEngine, Metrics, MMR reranking
│  │  │  ├─ embedders.py   
│  │  │  ├─ stores.py      
│  │  │  └─ llms.py        
│  │  ├─ shared/           # Shared utilities
│  │  │  ├─ __init__.py
│  │  │  └─ helpers.py     
│  │  ├─ __init__.py
│  │  └─ tests/
│  │     ├─ conftest.py        # pytest fixtures & setup
│  │     ├─ unit/              # unit tests for isolated logic
│  │     │  ├─ test_ingest.py  # chunking, doc loading, build_chunks tests
│  │     │  ├─ test_rag_core.py # RAGEngine initialization tests
│  │     │  └─ test_shared_helpers.py # convert_to_uuid tests
│  │     └─ integration/       # integration tests for API flows
│  │        ├─ test_api.py     # ingest, metrics, ask endpoints
│  │        ├─ test_acceptance_queries.py # acceptance criteria validation
│  │        ├─ test_fallback.py # Qdrant fallback to InMemoryStore
│  │        └─ test_rag_llms.py # LLM provider tests (OpenAI, future: Ollama)
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  ├─ app/
│  │  ├─ page.tsx         # main page layout
│  │  ├─ layout.tsx       # root layout with ToastProvider
│  │  └─ globals.css      # Tailwind directives + CSS variables + animations
│  ├─ components/
│  │  ├─ ui/              # reusable UI components
│  │  │  └─ Toast.tsx      # toast notification component
│  │  └─ features/        # feature-specific components
│  │     ├─ Chat.tsx      # chat interface with citations & chunk expansion
│  │     ├─ AdminPanel.tsx # ingestion controls + metrics display
│  │     └─ MetricsDisplay.tsx # formatted metrics visualization
│  ├─ contexts/            # React Context providers
│  │  ├─ ToastProvider.tsx # toast context & state management
│  │  └─ MetricsProvider.tsx # metrics context for shared state
│  ├─ lib/
│  │  ├─ api/              # API client
│  │  │  └─ client.ts      # type-safe API client with error handling
│  │  ├─ utils/            # utilities
│  │  │  └─ cn.ts          # className utility (clsx + tailwind-merge)
│  │  └─ types/            # TypeScript type definitions
│  │     └─ api.ts         # API request/response types (matches backend schemas)
│  ├─ package.json
│  ├─ package-lock.json   # npm lockfile
│  ├─ tsconfig.json
│  ├─ next.config.js
│  ├─ tailwind.config.js  # Tailwind CSS configuration
│  ├─ postcss.config.js   # PostCSS configuration
│  ├─ next-env.d.ts       # Next.js type definitions
│  └─ Dockerfile
├─ data/                  # sample policy docs
├─ logs/                  # log files (created when LOG_FILE_PATH is set)
│  └─ app.log             # rotating log file (if file logging enabled)
├─ docker-compose.yml     # main compose file (production-like)
├─ docker-compose.dev.yml # dev overrides (hot-reload volumes)
├─ docker-compose.test.yml # test overrides (bind-mount for pytest)
├─ Makefile               # convenience commands (dev, dev-hot, test, test-hot)
├─ .env.example           # environment variable template
```

## Tests

### Running Tests

**Using Makefile (Recommended)**:
```bash
# Run all tests
make test

# Run with hot-reload (sees local edits without rebuild)
make test-hot
```

**Using Docker directly**:
```bash
# Run all tests
docker compose run --rm backend pytest -q

# Run with hot-reload (sees local edits without rebuild)
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest -q

# Run specific test file
docker compose run --rm backend pytest app/tests/integration/test_api.py -v

# Run specific test
docker compose run --rm backend pytest app/tests/integration/test_api.py::test_ingest_idempotent -v

# Run with verbose output
docker compose run --rm backend pytest -v

# Run only unit tests
docker compose run --rm backend pytest app/tests/unit/ -v

# Run only integration tests
docker compose run --rm backend pytest app/tests/integration/ -v
```

**Note**: Tests are designed to run in Docker containers with proper environment setup. Running tests locally without Docker may encounter issues due to missing dependencies, environment variables, or data directory paths.

### Test Structure

The test suite is organized into two layers:

- **`unit/`** — Fast, isolated tests for deterministic logic:
  - `test_ingest.py` — Chunking, document loading, `build_chunks_from_docs`
  - `test_rag_core.py` — RAGEngine initialization, agent guide loading
  - `test_shared_helpers.py` — `convert_to_uuid` utility function
  - These tests run quickly and guard core building blocks

- **`integration/`** — End-to-end API scenarios:
  - `test_api.py` — Ingest idempotency, metrics endpoint, ask endpoint
  - `test_acceptance_queries.py` — Acceptance criteria validation (citation requirements)
  - `test_fallback.py` — Qdrant fallback to InMemoryStore
  - `test_rag_llms.py` — LLM provider tests (OpenAI with mocks)
  - These tests ensure the full stack works correctly

### Test Coverage

The test suite covers:
- ✅ Document ingestion and chunking
- ✅ Idempotent ingestion (no duplicates)
- ✅ Metrics tracking and reporting
- ✅ Acceptance query validation (required citations)
- ✅ Qdrant fallback mechanism
- ✅ Error handling (missing data dir, API errors)
- ✅ LLM provider switching (OpenAI mock)
- ✅ Helper function correctness

### Example Test Output

```bash
$ docker compose run --rm backend pytest -q
...test_ingest.py::test_chunk_text_with_overlap PASSED
...test_rag_core.py::test_rag_engine_loads_agent_guide PASSED
...test_api.py::test_ingest_idempotent PASSED
...test_acceptance_queries.py::test_acceptance_queries_have_required_citation PASSED
...test_fallback.py::test_qdrant_fallback PASSED
...test_rag_llms.py::test_openai_llm_with_mock PASSED
==================== 15 passed in 2.34s ====================
```

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Chat UI    │  │ Admin Panel  │  │  Metrics Display     │  │
│  │              │  │              │  │                      │  │
│  │ - Ask Q&A    │  │ - Ingest     │  │ - Formatted Cards    │  │
│  │ - Citations  │  │ - Refresh    │  │ - Raw JSON (debug)   │  │
│  │ - Chunks     │  │              │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │
│         │                 │                                    │
│         └──────────┬──────┘                                    │
│                    │ HTTP/REST                                 │
│                    ▼                                           │
│         ┌──────────────────────┐                               │
│         │   API Client (TS)     │                              │
│         │  - Type-safe calls    │                              │
│         │  - Error handling     │                              │
│         └──────────┬────────────┘                              │
└────────────────────┼───────────────────────────────────────────┘
                     │
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Layer (app/api/)                        │   │
│  │  - routes.py: Route handlers                             │   │
│  │  - schemas.py: Pydantic models                           │   │
│  │  - POST /api/ingest  → Load & chunk documents            │   │
│  │  - POST /api/ask     → RAG query flow                    │   │
│  │  - GET  /api/metrics → System statistics                 │   │
│  │  - GET  /api/health  → Health check                      │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                   │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Ingest      │  │   RAGEngine  │  │   Metrics    │           │
│  │  (ingest/)   │  │   (rag/)     │  │   (rag/)     │           │
│  │              │  │              │  │              │           │
│  │ - Load docs  │  │ - Embed      │  │ - Latencies  │           │
│  │ - Chunk text │  │ - Retrieve   │  │ - Counts     │           │
│  │ - Hash       │  │ - Rerank     │  │ - Fallback   │           │
│  │ - Metadata   │  │ - Generate   │  └──────────────┘           │
│  └────┬─────────┘  └───────┬──────┘                             │
│       │                    │                                    │
│       │                    │                                    │
│       │    ┌───────────────┼───────────────┐                    │
│       │    │               │               │                    │
│       ▼    ▼               ▼               ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Local        │  │  Vector      │  │  LLM         │           │
│  │ Embedder     │  │  Store       │  │  Provider    │           │
│  │ (embedders)  │  │  (stores)    │  │  (llms)      │           │
│  │              │  │              │  │              │           │
│  │ - Hash-      │  │ - Qdrant     │  │ - StubLLM    │           │
│  │   based      │  │   (primary)  │  │   (default)  │           │
│  │ - 384dim     │  │ - InMemory   │  │ - OpenAILLM  │           │
│  │              │  │   (fallback) │  │   (optional) │           │
│  └──────────────┘  └──────┬───────┘  └──────────────┘           │
│                           │                                     │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                        │ gRPC/HTTP
                        ▼
         ┌───────────────────────────────┐
         │    Qdrant (Vector DB)         │
         │                               │
         │  - Stores embeddings          │
         │  - Cosine similarity search   │
         │  - Collection: policy_helper  │
         └───────────────────────────────┘

Data Flow:
1. Ingest: Documents → Chunk → Embed → Store (Qdrant/InMemory)
2. Ask: Query → Embed → Search → Rerank (MMR) → Generate → Response
3. Metrics: Track latencies, counts, fallback status
```

## Notes
- Keep it simple. For take-home, focus on correctness, citations, and clean code.

---

## Candidate Instructions (Read Me First)

### Goal
Build a local-first **Policy & Product Helper** using RAG that:
- Ingests the sample docs under `/data`
- Answers questions with **citations** (title + section)
- Exposes metrics and health endpoints
- Provides a minimal **chat UI** and **admin panel**

You have **48 hours** once you start. AI coding tools are allowed.

### Deliverables
1. **GitHub repo link** with your changes.
2. **README** describing setup, architecture, trade-offs, and what you’d ship next.
3. **2–5 minute screen capture** demonstrating ingestion + Q&A + citations.
4. **Tests**: show how to run them and their results (e.g., `pytest -q`).

### Acceptance Checks (we will run)
1. `docker compose up --build` boots **Qdrant + backend + frontend**.
2. Use Admin tab to **ingest** docs without errors.
3. Ask: *“Can a customer return a damaged blender after 20 days?”* → cites **Returns_and_Refunds.md** and **Warranty_Policy.md**.
4. Ask: *“What’s the shipping SLA to East Malaysia for bulky items?”* → cites **Delivery_and_Shipping.md** (mentions bulky item surcharge).
5. Expand a citation chip and see the underlying chunk text.

### Rubric (100 pts)
- **Functionality & correctness (35)** — ingestion, RAG with citations, metrics, health.
- **Code quality & structure (20)** — small functions, separation of concerns, typing, linting.
- **Reproducibility & docs (15)** — clear README, env.example, diagrams.
- **UX & DX polish (10)** — responsive, accessible, solid loading/errors.
- **Testing (10)** — meaningful unit/integration tests that run locally.
- **Performance & observability (10)** — reasonable latency, useful metrics/logs.

### How to Run (Docker)
```bash
# copy env
cp .env.example .env

# run all services
docker compose up --build

# endpoints
# frontend: http://localhost:3000
# backend swagger: http://localhost:8000/docs
# qdrant ui: http://localhost:6333
```

### How to Run (No Docker, optional)
Backend:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
Frontend:
```bash
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

### Switching LLMs
- Default is **stub** (deterministic, offline).
- To use OpenAI: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY` in `.env`. (You are required to demo with OpenAI, API key is provided)
- To use Ollama: set `LLM_PROVIDER=stub` (keep stub) or extend `app/rag/llms.py` to add an `OllamaLLM` class following the same interface as `StubLLM` and `OpenAILLM`.
- All LLM providers receive the same `agent_guide` (internal SOP) and `required_output_format` for consistent behavior.
- Please document any changes you make.

### Vector Store
- Default is **Qdrant** via Docker. Fallback is in-memory if Qdrant isn't available.
- To switch to in-memory explicitly: `VECTOR_STORE=memory` in `.env`.

### Logging Configuration
- **Log Level**: Set `LOG_LEVEL` in `.env` (options: `DEBUG`, `INFO`, `WARNING`, `ERROR`). Default is `INFO`.
  - **Log Level Hierarchy**: Python logging uses a hierarchical system where setting a level shows that level and all higher levels:
    - `DEBUG` — Shows all messages (most verbose): debug details, info, warnings, errors
    - `INFO` — Shows important operations (default): API requests, ingestion, retrieval, generation, warnings, errors
    - `WARNING` — Shows warnings and errors only: fallbacks, initialization failures, file loading errors
    - `ERROR` — Shows errors only (least verbose): exceptions with full stack traces
  - **Example**: If `LOG_LEVEL=INFO`, you'll see INFO, WARNING, and ERROR messages, but DEBUG messages will be hidden.
- **File Logging**: Optionally set `LOG_FILE_PATH` in `.env` (e.g., `/app/logs/app.log`) to enable persistent file logging alongside console output. Log files are automatically rotated (10MB per file, 5 backups) to prevent disk space issues. The log directory is automatically created if it doesn't exist.
- **Log Location**: When `LOG_FILE_PATH` is set, logs are written to both console (visible in `docker compose logs`) and the specified file. Log files are accessible from the host at `./logs/` (mounted volume).
- **Viewing Logs**:
  - Console: `docker compose logs -f backend`
  - File: `tail -f logs/app.log` (if `LOG_FILE_PATH` is set)
- **What Gets Logged**: All key operations are logged with appropriate levels:
  - **DEBUG**: Detailed flow (chunk counts, search results, timing, skipped files)
  - **INFO**: Important operations (API requests, ingestion start/complete, configuration)
  - **WARNING**: Fallbacks (Qdrant → InMemory, OpenAI → Stub), file loading issues
  - **ERROR**: Exceptions with full stack traces (API errors, retrieval failures, generation errors)

### Configuration Reference

All configuration is done via environment variables in `.env`. Here's a complete reference:

#### LLM Configuration
- **`LLM_PROVIDER`** (default: `stub`)
  - Options: `stub` (deterministic, offline), `openai`, `ollama`
  - Determines which LLM provider to use
- **`OPENAI_API_KEY`** (optional)
  - Required if `LLM_PROVIDER=openai`
  - Your OpenAI API key for GPT-4o-mini
- **`OLLAMA_HOST`** (default: `http://ollama:11434`)
  - Ollama server URL (if using Ollama provider)

#### Vector Store Configuration
- **`VECTOR_STORE`** (default: `qdrant`)
  - Options: `qdrant` (primary, via Docker), `memory` (fallback, in-memory)
  - If Qdrant is unavailable, automatically falls back to `memory`
- **`COLLECTION_NAME`** (default: `policy_helper`)
  - Qdrant collection name for storing embeddings

#### Embedding Configuration
- **`EMBEDDING_MODEL`** (default: `local-384`)
  - Currently only `local-384` (hash-based, 384 dimensions) is supported
  - Future: could support OpenAI embeddings

#### Chunking Configuration
- **`CHUNK_SIZE`** (default: `700`)
  - Number of words per chunk
  - Larger chunks = more context but fewer chunks
- **`CHUNK_OVERLAP`** (default: `80`)
  - Number of words to overlap between consecutive chunks
  - Prevents context loss at chunk boundaries

#### Data Configuration
- **`DATA_DIR`** (default: `/app/data`)
  - Directory containing policy documents (`.md` and `.txt` files)
  - In Docker: mounted from `./data` on host

#### Logging Configuration
- **`LOG_LEVEL`** (default: `INFO`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - Controls verbosity of logs (see Logging Configuration section)
- **`LOG_FILE_PATH`** (optional)
  - Path to log file (e.g., `/app/logs/app.log`)
  - If set, logs are written to both console and file
  - Leave empty for console-only logging

#### Frontend Configuration
- **`NEXT_PUBLIC_API_BASE`** (default: `http://localhost:8000`)
  - Backend API base URL for frontend
  - Must be accessible from the browser

### API Reference

Complete API documentation with request/response examples:

#### `GET /api/health`
Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

#### `GET /api/metrics`
Get system metrics and statistics.

**Response** (200 OK):
```json
{
  "total_docs": 5,
  "total_chunks": 11,
  "ask_count": 3,
  "fallback_used": false,
  "avg_retrieval_latency_ms": 12.34,
  "avg_generation_latency_ms": 45.67,
  "embedding_model": "local-384",
  "llm_model": "stub"
}
```

**Error Response** (500):
```json
{
  "detail": "Error fetching metrics: <error message>"
}
```

#### `POST /api/ingest`
Ingest documents from the data directory.

**Request**: No body required

**Response** (200 OK):
```json
{
  "indexed_docs": 5,
  "indexed_chunks": 11
}
```

**Error Responses**:
- **404 Not Found**: Data directory not found
  ```json
  {
    "detail": "Data directory not found: /app/data"
  }
  ```
- **500 Internal Server Error**: Ingestion failed
  ```json
  {
    "detail": "Error ingesting documents: <error message>"
  }
  ```

#### `POST /api/ask`
Ask a question and get an answer with citations.

**Request Body**:
```json
{
  "query": "What's the shipping SLA to East Malaysia for bulky items?",
  "k": 4
}
```

**Parameters**:
- `query` (required): The question to ask
- `k` (optional, default: 4): Number of chunks to retrieve and use for context

**Response** (200 OK):
```json
{
  "query": "What's the shipping SLA to East Malaysia for bulky items?",
  "answer": "Answer (stub):\nBased on the policy documents below...",
  "citations": [
    {
      "title": "Delivery_and_Shipping.md",
      "section": "SLA"
    }
  ],
  "chunks": [
    {
      "title": "Delivery_and_Shipping.md",
      "section": "SLA",
      "text": "West Malaysia: 2–4 business days..."
    }
  ],
  "metrics": {
    "total_docs": 5,
    "total_chunks": 11,
    "ask_count": 1,
    "fallback_used": false,
    "avg_retrieval_latency_ms": 12.34,
    "avg_generation_latency_ms": 45.67,
    "embedding_model": "local-384",
    "llm_model": "stub",
    "retrieval_ms": 12.34,
    "generation_ms": 45.67
  }
}
```

**Error Response** (500):
```json
{
  "detail": "Error processing query: <error message>"
}
```

**Note**: The `metrics` field in the response contains the full `MetricsResponse` plus legacy fields (`retrieval_ms`, `generation_ms`) for backward compatibility.

### UI Walkthrough
1. Open **http://localhost:3000**.
2. In **Admin** panel:
   - Click **Ingest sample docs** button (shows loading spinner during indexing)
   - Success toast appears: "Documents ingested successfully"
   - Metrics cards update automatically showing indexed documents and chunks count
   - Click **Refresh metrics** to manually update
   - View formatted metrics in color-coded cards or expand "View raw metrics (debug)" for JSON
3. In **Chat** panel:
   - Type a question and press Enter (or click Send button)
   - User message appears in blue bubble on the right
   - Loading indicator shows "Thinking..." while processing
   - Assistant response appears in white card on the left with:
     - Answer text
     - Citation badges (with document icons) showing source documents
     - "View supporting chunks" toggle button showing chunk count
   - Click citation badges to see tooltip with section name
   - Click "View supporting chunks" to expand/collapse underlying chunk text
   - Success/error toasts appear at top-center for feedback
4. **Accessibility features**:
   - All buttons have ARIA labels
   - Keyboard navigation: Tab to navigate, Enter to submit
   - Focus states visible with ring indicators
   - Screen reader friendly with semantic HTML

### What You Can Modify
- Anything. Improve chunking, reranking (MMR), prompt, UI polish, streaming, caching, guardrails (PDPA masking), feedback logging, small eval script, etc.
- Keep the one-command run and README accurate.

### Backend Tech Stack
- **FastAPI** — Modern Python web framework for building REST APIs with automatic OpenAPI documentation
- **Python 3.11** — Programming language with type hints and modern async support
- **Pydantic** — Data validation and settings management using Python type annotations
- **Uvicorn** — ASGI server for running FastAPI applications
- **Qdrant Client** — Python client for Qdrant vector database operations
- **OpenAI SDK** — Official Python SDK for OpenAI API integration
- **NumPy** — Numerical computing library for embedding vector operations
- **Pytest** — Testing framework for unit and integration tests
- **Python logging** — Built-in logging module with configurable levels and rotating file handlers

### Backend Architecture
- **Modular code structure**: Organized into clear module boundaries for scalability:
  - `app/api/` — API layer (routes, schemas) separated from business logic
  - `app/ingest/` — Document ingestion (core, helpers, utils) for loading and chunking documents
  - `app/rag/` — RAG engine (core, embedders, stores, llms) for retrieval and generation
  - `app/shared/` — Shared utilities (convert_to_uuid, common helpers)
  - This structure makes it easy to extend (add routes, new LLM providers, new stores) and test components in isolation
- **Dependency injection**: `RAGEngine` is injected into API routes via `set_engine()` pattern, enabling easy testing and configuration
- **Provider pattern**: Pluggable LLM providers (StubLLM, OpenAILLM) and vector stores (QdrantStore, InMemoryStore) with automatic fallback
- **Type safety**: Pydantic models for request/response validation and type checking throughout
- **Error handling**: Comprehensive try-except blocks with structured logging at all layers
- **Configuration management**: Centralized settings via Pydantic `Settings` class with environment variable support

### Frontend Tech Stack
- **Next.js 14** — React framework with App Router
- **TypeScript** — Type-safe development with interfaces matching backend models
- **Tailwind CSS** — Utility-first CSS framework with semantic color tokens
- **lucide-react** — Icon library for consistent visual language
- **React Context** — Toast state management via `ToastProvider`
- **Custom hooks** — `useToast()` for accessing toast functionality throughout the app

### Frontend Architecture
- **Modular component structure**: Organized into clear module boundaries:
  - `components/ui/` — Reusable UI components (Toast)
  - `components/features/` — Feature-specific components (Chat, AdminPanel, MetricsDisplay)
  - `contexts/` — React Context providers (ToastProvider, MetricsProvider)
  - `lib/api/` — API client (`client.ts`) with centralized error handling
  - `lib/utils/` — Utility functions (`cn.ts` for className merging)
  - `lib/types/` — TypeScript type definitions matching backend schemas
- **State management**: React hooks (`useState`, `useCallback`, `useRef`) for local state; Context API for global state (toast notifications, metrics)
- **Type safety**: TypeScript interfaces in `lib/types/api.ts` match backend Pydantic models exactly, ensuring compile-time type safety
- **Styling**: Tailwind utility classes with CSS variables for theming; custom animations in `globals.css`
- **Accessibility**: ARIA labels, keyboard navigation, focus states, semantic HTML throughout

### Constraints & Notes
- Keep keys out of the frontend.
- Validate file types if you extend ingestion to uploads.
- Provide small architecture diagram if you can (ASCII is fine).

### Troubleshooting
- **Qdrant healthcheck failing**: ensure port `6333` is free; re-run compose.
- **CORS**: CORS is configured to `*` in `main.py` for local dev.
- **Embeddings/LLM**: With no keys, stub models run by default so the app always works.
- **Log files not created**: Ensure `LOG_FILE_PATH` is set in `.env` and the path is accessible. Check that `docker-compose.yml` includes the `LOG_FILE_PATH` environment variable. Log files are created in the container at the specified path and accessible from the host via the `./logs` volume mount.
- **Viewing logs**: Use `docker compose logs backend` for console logs, or `tail -f logs/app.log` for file logs (if `LOG_FILE_PATH` is configured).

## Current Enhancements

This section documents the enhancements and improvements made during the assessment:

### Backend Enhancements
- **Deterministic chunk IDs + dedupe** — `QdrantStore.upsert` now converts chunk hashes into UUIDs and `RAGEngine` tracks `_chunk_hashes`, so re-ingesting the same docs is a no-op (no duplicate points, accurate `indexed_docs/chunks`, stable metrics).
- **MMR reranking for retrieval quality** — `RAGEngine.retrieve()` now applies Maximal Marginal Relevance (MMR) reranking to balance relevance and diversity. Fetches 2x candidates initially, then reranks to avoid redundant chunks while keeping the most relevant results. Lambda parameter (0.7) favors relevance over pure diversity. Only exact duplicates (same title + section) are penalized, allowing different sections from the same document to both be included when relevant.
- **Metadata-enriched chunks for intelligent retrieval** — Chunks now include metadata (`heading_level`, `section_priority`) that enriches the chunk data structure and enables intelligent boosting during MMR reranking. Heading levels (H1=1.2x boost, H2=1.15x boost, H3=1.1x boost) and section priorities (high=1.15x, medium=1.05x) are automatically detected from document structure and section titles. High-priority sections (SLA, Policy, Terms, Conditions, Refund, Warranty, Compliance) receive score multipliers, ensuring semantically important chunks are more likely to be retrieved for relevant queries. This improves both chunk quality (richer metadata) and retrieval accuracy (intelligent boosting).
- **Enhanced metrics tracking** — `RAGEngine` now tracks `ask_count` (incremented in `generate()`) and `fallback_used` (set when Qdrant fails). Both fields included in `MetricsResponse` and returned in `/api/ask` response for real-time frontend updates.
- **Internal SOP as system instructions (not retrievable policy)** — `Internal_SOP_Agent_Guide.md` is treated as internal behavior guidance for the agent, not as a user-facing policy document. It is explicitly excluded from ingestion in `load_documents`, so it never appears as a retrieved chunk or citation. Instead, `RAGEngine` loads its contents once at startup into `agent_guide` and passes it into all LLM providers (stub + OpenAI) as part of the system prompt. This means the agent follows the SOP (tone, no hallucinations, cite sources, escalate when unsure) without exposing the guide itself to end users.
- **Structured prompt architecture with consistent output format** — LLM prompts now use a proper system/user message split (following OpenAI best practices). The system prompt contains: base role definition, internal SOP rules (if present), and a required output format specification (`Answer / Sources / Details`). The user prompt contains only the question and retrieved context. The output format is defined once in `RAGEngine.required_output_format` and passed to all LLM providers (StubLLM, OpenAILLM, and future providers like Ollama), ensuring consistent formatting across all modes. This DRY approach makes it easy to change the format in one place and guarantees that stub, OpenAI, and any future LLM implementations produce answers with the same structure.
- **Layered automated coverage** — Test suite reorganized into unit vs integration:
  - Unit layer protects deterministic building blocks (`convert_to_uuid`, chunking, doc loaders, metrics math), and is easy to extend as more logic gets isolated.
  - Integration layer covers ingest idempotency, metrics, acceptance queries, Qdrant-down fallback, ingest error-path (JSON + CORS), and a mocked OpenAI-mode smoke test so provider switching is guarded without real API calls.
- **Modular code structure** — Backend refactored into clear module boundaries for scalability:
  - `app/api/` — API layer (routes, schemas) separated from business logic
  - `app/ingest/` — Document ingestion (core, helpers, utils)
  - `app/rag/` — RAG engine (core, embedders, stores, llms)
  - `app/shared/` — Shared utilities (convert_to_uuid)
  - This structure makes it easy to extend (add routes, new LLM providers, new stores) and test components in isolation.
- **Acceptance checks baked into tests** — `tests/integration/test_acceptance_queries.py` programmatically verifies the "damaged blender" and "East Malaysia SLA" prompts cite the mandated documents and contain required content (e.g., "bulky items" mention), matching the rubric expectations.
- **Comprehensive logging with dual output** — Structured logging throughout the backend with configurable log levels (DEBUG, INFO, WARNING, ERROR). Logs are written to both console (stdout/stderr) for real-time viewing and optionally to rotating log files for persistence. File logging uses `RotatingFileHandler` (10MB per file, 5 backups) to prevent disk space issues. All key operations are logged: API requests/responses, RAG operations (ingestion, retrieval, generation), vector store operations, LLM calls, and errors with full stack traces. Logs include timestamps, module names, and contextual information (query previews, chunk counts, latencies) for effective debugging and monitoring. This enhances observability and aligns with production-ready practices.

### Frontend Enhancements
- **Toast notification system** — Global toast notifications (top-center) provide user feedback for all async operations (ingestion, ask queries, errors). Auto-dismisses after 5 seconds with manual dismiss option. Three variants: success (green), error (red), info (blue) with appropriate icons from `lucide-react`.
- **Enhanced error handling** — API client (`lib/api/client.ts`) extracts detailed error messages from FastAPI responses (checks `detail` and `message` fields), providing actionable feedback instead of generic "Request failed" messages. Errors are shown both in toasts and inline in chat.
- **Improved citation UX** — Citation badges now feature icons, subtle color accents, and better visual hierarchy. Chunk expansion uses toggle buttons with chevron indicators, showing chunk count. Expanded chunks display in formatted cards with clear title/section separation.
- **Metrics visualization** — `MetricsDisplay` component shows all backend metrics in a responsive 2x2 grid with color-coded cards (blue for docs, purple for chunks, green for questions, indigo/amber for vector store). Each card includes an icon and formatted numbers. Raw JSON available in collapsible debug section.
- **Real-time metrics updates** — `MetricsProvider` context manages shared metrics state across the app. When Chat asks questions, metrics (ask_count, latencies) update automatically in AdminPanel without manual refresh. Backend `/api/ask` endpoint includes full `MetricsResponse` in response, enabling seamless frontend updates.
- **Loading states & accessibility** — All buttons show loading spinners during async operations. Inputs are disabled during loading to prevent duplicate submissions. Full keyboard navigation support (Enter to send, Shift+Enter for newline). ARIA labels on all interactive elements. Visible focus states with ring indicators.
- **Responsive design & typography** — Mobile-first responsive layout using Tailwind CSS breakpoints. Improved typography scale, spacing, and touch targets. Chat messages use max-width constraints and proper text wrapping. Metrics grid adapts from 1 column (mobile) to 2 columns (desktop).
- **Type-safe API layer** — TypeScript interfaces in `lib/types/api.ts` (`AskResponse`, `MetricsResponse`, `IngestResponse`, `Citation`, `Chunk`) match backend Pydantic models exactly, ensuring compile-time type safety and preventing field name mismatches.
- **Modern styling system** — Migrated from inline styles to Tailwind CSS with semantic color tokens via CSS variables. Enables easy theming and consistent design system. Custom animations for toasts and loading spinners defined in `globals.css`.
- **Modular code structure** — Frontend refactored into clear module boundaries for scalability:
  - `components/ui/` — Reusable UI components (Toast)
  - `components/features/` — Feature-specific components (Chat, AdminPanel, MetricsDisplay)
  - `contexts/` — React Context providers (ToastProvider, MetricsProvider)
  - `lib/api/` — API client with centralized error handling
  - `lib/utils/` — Utility functions (className merging)
  - `lib/types/` — Centralized TypeScript type definitions matching backend schemas
  - This structure makes it easy to extend (add new features, components, API endpoints) and maintain clear separation of concerns.

### Next Steps

If given more time or planning for production deployment, here are potential enhancements:

#### Performance Optimizations
- **Async embeddings**: Use async/await for batch embedding operations to improve ingestion speed
- **Caching**: Add response caching for frequently asked questions to reduce LLM API calls
- **Streaming responses**: Implement Server-Sent Events (SSE) for streaming LLM responses to improve perceived latency
- **Batch processing**: Process multiple queries in parallel for better throughput

#### Production Readiness
- **Authentication**: Add API key authentication or OAuth for production use
- **Rate limiting**: Implement rate limiting to prevent abuse and manage costs
- **Monitoring**: Integrate with monitoring tools (Prometheus, Grafana) for metrics visualization
- **Error tracking**: Add error tracking service (Sentry) for production error monitoring
- **Health checks**: Enhanced health checks that verify Qdrant connectivity and data availability

#### Feature Enhancements
- **Document upload UI**: Allow users to upload and ingest custom documents via the frontend
- **Multi-language support**: Add support for documents and queries in multiple languages
- **Conversation history**: Persist chat history and allow users to view past conversations
- **Export functionality**: Allow users to export conversations or citations as PDF/JSON
- **Advanced search**: Add semantic search with filters (by document, date range, etc.)

#### RAG Improvements
- **Hybrid search**: Combine semantic search with keyword search for better recall
- **Query expansion**: Automatically expand queries with synonyms or related terms
- **Re-ranking models**: Use cross-encoder models for more accurate reranking
- **Chunk optimization**: Implement adaptive chunking based on document structure
- **Embedding models**: Support multiple embedding models (OpenAI, sentence-transformers) with comparison

#### Evaluation & Quality
- **Eval framework**: Build evaluation scripts to measure answer quality, citation accuracy, and latency
- **A/B testing**: Compare different chunking strategies, reranking parameters, or LLM prompts
- **Feedback loop**: Allow users to rate answers and use feedback to improve retrieval
- **Citation validation**: Automatically verify that citations actually contain the claimed information

#### Developer Experience
- **API documentation**: Enhanced Swagger/OpenAPI docs with examples and schemas
- **Development tools**: Add scripts for data migration, bulk ingestion, or testing
- **Configuration UI**: Admin panel for adjusting chunking parameters, LLM settings without code changes
- **Debug mode**: Enhanced debugging tools for inspecting retrieval results and prompt construction

### Submission
- Share GitHub repo link + your short demo video.
- Include any notes on trade-offs and next steps.
