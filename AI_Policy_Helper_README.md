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
│  │  ├─ Chat.tsx         # chat interface with citations & chunk expansion
│  │  ├─ AdminPanel.tsx   # ingestion controls + metrics display
│  │  ├─ MetricsDisplay.tsx # formatted metrics visualization
│  │  ├─ Toast.tsx        # toast notification component
│  │  ├─ ToastProvider.tsx # toast context & state management
│  │  └─ MetricsProvider.tsx # metrics context for shared state
│  ├─ lib/
│  │  ├─ api.ts           # type-safe API client with error handling
│  │  └─ utils.ts         # className utility (cn)
│  ├─ package.json
│  ├─ package-lock.json   # npm lockfile
│  ├─ tsconfig.json
│  ├─ next.config.js
│  ├─ tailwind.config.js  # Tailwind CSS configuration
│  ├─ postcss.config.js   # PostCSS configuration
│  ├─ next-env.d.ts       # Next.js type definitions
│  └─ Dockerfile
├─ data/                  # sample policy docs
├─ docker-compose.yml     # main compose file (production-like)
├─ docker-compose.dev.yml # dev overrides (hot-reload volumes)
├─ docker-compose.test.yml # test overrides (bind-mount for pytest)
├─ Makefile               # convenience commands (dev, dev-hot, test, test-hot)
├─ .env.example           # environment variable template
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

## Current Enhancements & Guardrails

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

### Frontend Enhancements
- **Toast notification system** — Global toast notifications (top-center) provide user feedback for all async operations (ingestion, ask queries, errors). Auto-dismisses after 5 seconds with manual dismiss option. Three variants: success (green), error (red), info (blue) with appropriate icons from `lucide-react`.
- **Enhanced error handling** — API client (`lib/api.ts`) extracts detailed error messages from FastAPI responses (checks `detail` and `message` fields), providing actionable feedback instead of generic "Request failed" messages. Errors are shown both in toasts and inline in chat.
- **Improved citation UX** — Citation badges now feature icons, subtle color accents, and better visual hierarchy. Chunk expansion uses toggle buttons with chevron indicators, showing chunk count. Expanded chunks display in formatted cards with clear title/section separation.
- **Metrics visualization** — `MetricsDisplay` component shows all backend metrics in a responsive 2x2 grid with color-coded cards (blue for docs, purple for chunks, green for questions, indigo/amber for vector store). Each card includes an icon and formatted numbers. Raw JSON available in collapsible debug section.
- **Real-time metrics updates** — `MetricsProvider` context manages shared metrics state across the app. When Chat asks questions, metrics (ask_count, latencies) update automatically in AdminPanel without manual refresh. Backend `/api/ask` endpoint includes full `MetricsResponse` in response, enabling seamless frontend updates.
- **Loading states & accessibility** — All buttons show loading spinners during async operations. Inputs are disabled during loading to prevent duplicate submissions. Full keyboard navigation support (Enter to send, Shift+Enter for newline). ARIA labels on all interactive elements. Visible focus states with ring indicators.
- **Responsive design & typography** — Mobile-first responsive layout using Tailwind CSS breakpoints. Improved typography scale, spacing, and touch targets. Chat messages use max-width constraints and proper text wrapping. Metrics grid adapts from 1 column (mobile) to 2 columns (desktop).
- **Type-safe API layer** — TypeScript interfaces (`AskResponse`, `MetricsResponse`, `IngestResponse`) match backend Pydantic models exactly, ensuring compile-time type safety and preventing field name mismatches.
- **Modern styling system** — Migrated from inline styles to Tailwind CSS with semantic color tokens via CSS variables. Enables easy theming and consistent design system. Custom animations for toasts and loading spinners defined in `globals.css`.

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

### Frontend Tech Stack
- **Next.js 14** — React framework with App Router
- **TypeScript** — Type-safe development with interfaces matching backend models
- **Tailwind CSS** — Utility-first CSS framework with semantic color tokens
- **lucide-react** — Icon library for consistent visual language
- **React Context** — Toast state management via `ToastProvider`
- **Custom hooks** — `useToast()` for accessing toast functionality throughout the app

### Frontend Architecture
- **Component structure**: Modular components (`Chat`, `AdminPanel`, `MetricsDisplay`, `Toast`) with clear separation of concerns
- **State management**: React hooks (`useState`, `useCallback`, `useRef`) for local state; Context API for global toast state
- **API layer**: Type-safe client in `lib/api.ts` with centralized error handling
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

### Submission
- Share GitHub repo link + your short demo video.
- Include any notes on trade-offs and next steps.
