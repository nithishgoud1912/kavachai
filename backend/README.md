# KavachAI Backend — Sovereign Industrial Agentic AI Workbench

## Section 1 Decisions (recorded per backend_building.md §1)

| # | Question | Decision |
|---|---|---|
| 1 | Demo corpus | Synthetic, drafted for approval |
| 2 | LLM | Qwen 2.5 3B via Ollama |
| 3 | Hardware | RTX 3050 6GB VRAM, 16GB DDR5 |
| 4 | Embedding model | nomic-embed-text (768d) |
| 5 | Vision/VLM | Pre-computed graph fallback |
| 6 | Vector DB | ChromaDB |
| 7 | Deployment | Docker + NVIDIA runtime |
| 8 | Ports | Backend :8000, Frontend :3000, HTTP |
| 9 | Frontend | Teammate builds in parallel |
| 10 | Session storage | SQLite |
| 11 | Graph scope | 4 nodes: T-101→P-102→V-204→R-101 |

## Quick Start

```bash
# 1. Copy and edit env
cp .env.example .env

# 2. Ensure Ollama is running with required models
ollama pull qwen2.5:3b
ollama pull nomic-embed-text

# 3. Run with Docker
docker-compose up --build

# 4. Or run directly
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

See `backend_building.md` for the full phased build plan.
See `API_Reference.md` for the REST/SSE contract.
See `SRS.md` §3 for requirement traceability (every module comments its FR/NFR IDs).
