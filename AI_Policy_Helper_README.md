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

- `make dev-hot` → runs `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`, bind-mounting `backend/app` and the frontend workspace so Uvicorn (`--reload`) and Next.js (`npm run dev`) hot-reload as you edit.
- `make test-hot` → runs `docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest -q`, which bind-mounts `backend/app` during the test command so pytest sees your latest files without rebuilding.
- `make dev` → original `docker compose up --build` path, useful for a final prod-style verification.

## Offline-friendly
- If you **don’t** set an API key, the backend uses a **deterministic stub LLM** and a **built-in embedding** to keep everything fully local.
- If you set `OPENAI_API_KEY` (or configure Ollama), the backend will use real models automatically.

## Project layout
```
ai-policy-helper/
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI app + endpoints
│  │  ├─ settings.py      # config/env
│  │  ├─ rag.py           # embeddings, vector store, retrieval, generation
│  │  ├─ models.py        # pydantic models
│  │  ├─ ingest.py        # doc loader & chunker
│  │  ├─ __init__.py
│  │  └─ tests/
│  │     ├─ conftest.py
│  │     └─ test_api.py
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  ├─ app/
│  │  ├─ page.tsx         # chat UI
│  │  ├─ layout.tsx
│  │  └─ globals.css
│  ├─ components/
│  │  ├─ Chat.tsx
│  │  └─ AdminPanel.tsx
│  ├─ lib/api.ts
│  ├─ package.json
│  ├─ tsconfig.json
│  ├─ next.config.js
│  └─ Dockerfile
├─ data/                  # sample policy docs
├─ docker-compose.yml
├─ Makefile
└─ .env.example
```

## Tests
Run unit/integration suites inside the backend container:
```bash
docker compose run --rm backend pytest -q
# reproducible run against the last-built image
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest -q
# bind-mounts backend/app so local edits are picked up without rebuilding
```
- Test structure (`backend/app/tests/`):
  - `unit/` — fast checks for deterministic logic (chunking, hash→UUID, doc loaders, metrics math, etc.) so small building blocks stay correct.
  - `integration/` — end-to-end API scenarios (ingest, metrics, acceptance prompts, fallback, error paths, OpenAI provider) to ensure the deployed stack keeps working.

## Notes
- Keep it simple. For take-home, focus on correctness, citations, and clean code.

---

## Current Enhancements & Guardrails
- **Deterministic chunk IDs + dedupe** — `QdrantStore.upsert` now converts chunk hashes into UUIDs and `RAGEngine` tracks `_chunk_hashes`, so re-ingesting the same docs is a no-op (no duplicate points, accurate `indexed_docs/chunks`, stable metrics).
- **MMR reranking for retrieval quality** — `RAGEngine.retrieve()` now applies Maximal Marginal Relevance (MMR) reranking to balance relevance and diversity. Fetches 2x candidates initially, then reranks to avoid redundant chunks while keeping the most relevant results. Lambda parameter (0.7) favors relevance over pure diversity. Only exact duplicates (same title + section) are penalized, allowing different sections from the same document to both be included when relevant.
- **Layered automated coverage** — Test suite reorganized into unit vs integration:
  - Unit layer protects deterministic building blocks (`_hash_to_uuid`, chunking, doc loaders, metrics math), and is easy to extend as more logic gets isolated.
  - Integration layer covers ingest idempotency, metrics, acceptance queries, Qdrant-down fallback, ingest error-path (JSON + CORS), and a mocked OpenAI-mode smoke test so provider switching is guarded without real API calls.
- **Acceptance checks baked into tests** — `tests/integration/test_acceptance_queries.py` programmatically verifies the “damaged blender” and “East Malaysia SLA” prompts cite the mandated documents and contain required content (e.g., “bulky items” mention), matching the rubric expectations.

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
- To use Ollama: set `LLM_PROVIDER=stub` (keep stub) or extend `rag.py` to add an `OllamaLLM` class.
- Please document any changes you make.

### Vector Store
- Default is **Qdrant** via Docker. Fallback is in-memory if Qdrant isn’t available.
- To switch to in-memory explicitly: `VECTOR_STORE=memory` in `.env`.

### API Reference
- `POST /api/ingest` → `{ indexed_docs, indexed_chunks }`
- `POST /api/ask` body:
  ```json
  { "query": "What's the refund window for Category A?", "k": 4 }
  ```
  Response includes `answer`, `citations[]`, `chunks[]`, `metrics`.
- `GET /api/metrics` → counters + avg latencies
- `GET /api/health` → `{ "status": "ok" }`

### UI Walkthrough
1. Open **http://localhost:3000**.
2. In **Admin** card, click **Ingest sample docs** and then **Refresh metrics**.
3. In **Chat**, ask questions. Click the **source badges** to expand supporting chunks.

### What You Can Modify
- Anything. Improve chunking, reranking (MMR), prompt, UI polish, streaming, caching, guardrails (PDPA masking), feedback logging, small eval script, etc.
- Keep the one-command run and README accurate.

### Constraints & Notes
- Keep keys out of the frontend.
- Validate file types if you extend ingestion to uploads.
- Provide small architecture diagram if you can (ASCII is fine).

### Troubleshooting
- **Qdrant healthcheck failing**: ensure port `6333` is free; re-run compose.
- **CORS**: CORS is configured to `*` in `main.py` for local dev.
- **Embeddings/LLM**: With no keys, stub models run by default so the app always works.

### Submission
- Share GitHub repo link + your short demo video.
- Include any notes on trade-offs and next steps.
