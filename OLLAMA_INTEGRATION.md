# Ollama Integration Guide

This document explains how to use Ollama as an LLM provider in the AI Policy Helper project.

## What Was Added

1. **Ollama Docker Service** - Added to `docker-compose.yml` to run Ollama in a container
2. **OllamaLLM Class** - New LLM provider implementation in `backend/app/rag/llms.py`
3. **RAGEngine Support** - Updated to detect and use Ollama when `LLM_PROVIDER=ollama`
4. **Configuration** - Added `OLLAMA_MODEL` environment variable for model selection

## Quick Start

Choose your setup method based on your platform:

### Option A: Native Ollama (Recommended on Mac)

> **Why native on Mac?** Docker Desktop on Mac doesn't support GPU acceleration. Docker Ollama on Mac runs CPU-only and is significantly slower. Native Ollama can use Mac's Metal GPU for much faster inference.

**Complete Workflow:**

1. **Install Ollama** (if not already installed):
   - Download from https://ollama.com/download
   - Launch the Ollama app

2. **Pull a model** (first time only):
   ```bash
   ollama pull qwen2.5:0.5b
   # Verify: ollama list
   ```

3. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_HOST=http://host.docker.internal:11434
   OLLAMA_MODEL=qwen2.5:0.5b  # Optional, defaults to qwen2.5:0.5b
   ```

4. **Start services**:
   ```bash
   docker compose down  # Optional: clean start
   make dev
   ```
   > **Note**: When using native Ollama, the Docker Ollama service won't start (saves resources). The backend will connect to your native Ollama instance via `OLLAMA_HOST`.

5. **Verify connection**:
   ```bash
   docker compose logs backend | grep -i ollama
   ```
   Should see: `"Using Ollama LLM provider (qwen2.5:0.5b)"`

6. **Test the app**:
   - Ingest documents: Click "Ingest sample docs" in Admin panel
   - Ask questions: Use the Chat interface
   - Check responses use Ollama instead of stub

### Option B: Docker Ollama

> **Note**: Works on Mac but runs CPU-only (no GPU acceleration), so it's slower than native. Use this if you prefer everything containerized, or if you're on Linux with NVIDIA GPU support.

**Complete Workflow:**

1. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=qwen2.5:0.5b  # Optional, defaults to qwen2.5:0.5b
   # OLLAMA_HOST defaults to http://ollama:11434 (Docker service)
   ```

2. **Start services with Docker Ollama**:
   ```bash
   docker compose down  # Optional: clean start
   make dev-ollama
   # Or: docker compose --profile docker-ollama up --build
   ```
   > **Note**: The Ollama Docker service is now optional. Use `make dev-ollama` to start it, or `make dev` if using native Ollama.

3. **Pull a model** (wait for services to start, first time only):
   ```bash
   make ollama-pull MODEL=qwen2.5:0.5b
   # Or manually: docker compose --profile docker-ollama exec ollama ollama pull qwen2.5:0.5b
   ```

4. **Verify connection**:
   ```bash
   docker compose logs backend | grep -i ollama
   ```

5. **Test the app**:
   - Ingest documents: Click "Ingest sample docs" in Admin panel
   - Ask questions: Use the Chat interface
   - Check responses use Ollama instead of stub

**Check available models:**
- Visit https://ollama.com/library
- Run `ollama list` (native) or `make ollama-list` (Docker)

## Available Models

Popular models you can use:
- `qwen2.5:0.5b` (default) - one of the smallest
- `llama3.2` - Fast, efficient, good for general tasks
- `mistral` - Strong performance, good reasoning
- `llama2` - Older but stable
- `codellama` - Specialized for code
- `phi3` - Small, fast model

See all available models: https://ollama.com/library or run `ollama list` to see what you have installed.

## Mac Users (Recommended Setup)

On Mac, Ollama **can** run in Docker, but it will be CPU-only and slower. Running Ollama natively (outside Docker) allows GPU acceleration via Metal, resulting in much better performance.

### Step-by-Step Mac Setup:

1. **Install Ollama** (if not already done):
   - Download from https://ollama.com/download
   - Install and launch the Ollama app
   - Verify it's running: `ollama list` should work in terminal

2. **Pull your model**:
   ```bash
   ollama pull qwen2.5:0.5b
   ```
   This will download the model (may take a few minutes, ~0.3GB).

3. **Update `.env` file**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_HOST=http://host.docker.internal:11434
   OLLAMA_MODEL=qwen2.5:0.5b
   ```

4. **Start services** (Ollama Docker service won't start - saves resources):
   ```bash
   make dev
   # Or: docker compose up --build
   ```
   > **Note**: The Ollama Docker service is now optional using profiles. When using native Ollama, it won't start automatically, saving disk space and memory.

5. **Verify connection**:
   - Check backend logs: `docker compose logs backend | grep Ollama`
   - Should see: "Using Ollama LLM provider (qwen2.5:0.5b)"

**Note**: If you see connection errors, ensure:
- Ollama app is running on your Mac
- `OLLAMA_HOST` is set to `http://host.docker.internal:11434`
- Model is pulled: `ollama list` should show your model

## Troubleshooting

### Model Not Found
If you see errors about model not found:
```bash
docker compose exec ollama ollama pull <model_name>
```

### Connection Errors
Check if Ollama is running:
```bash
docker compose ps ollama
docker compose logs ollama
```

### Slow Responses
- Ollama models run locally and may be slower than cloud APIs
- Try a smaller model like `phi3` or `llama3.2:1b` for faster responses
- Ensure you have enough RAM (models need 4-8GB+ depending on size)

## Architecture

The Ollama integration follows the same pattern as other LLM providers:

```
RAGEngine
  └─> OllamaLLM
       └─> HTTP POST to http://ollama:11434/api/chat
            └─> Returns generated answer
```

All LLM providers (Stub, OpenAI, Ollama) share:
- Same system/user message format
- Internal SOP integration
- Required output format enforcement
- Error handling with fallback to StubLLM

## Testing

To test Ollama integration:

1. Set `LLM_PROVIDER=ollama` in `.env`
2. Pull model: `ollama pull qwen2.5:0.5b` (or your chosen model)
3. Start services: `docker compose up --build`
4. Ingest: POST to `/api/ingest` or use UI
5. Ask: POST to `/api/ask` with a query or use Chat UI
6. Check response - should use Ollama instead of stub
7. Verify in logs: `docker compose logs backend | grep "Ollama"`

## Next Steps

- Add streaming support for real-time responses
- Add model health checks
- Support multiple models with automatic fallback
- Add model performance metrics

