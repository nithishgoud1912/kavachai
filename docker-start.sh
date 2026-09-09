#!/usr/bin/env bash
set -e

echo "================================================"
echo "  Starting KavachAI Sovereign AI Stack (Docker) "
echo "================================================"

# 1. Ensure .env exists
if [ ! -f ".env" ]; then
    echo "[1/4] Creating .env from .env.example..."
    cp .env.example .env
fi

# 2. Build and start services
echo "[2/4] Building and launching containers..."
docker compose up -d --build

# 3. Pull required Ollama models
echo "[3/4] Ensuring Ollama models are pulled..."
docker compose exec -T ollama ollama pull qwen2.5:3b
docker compose exec -T ollama ollama pull nomic-embed-text

echo "[4/4] All services are up!"
echo ""
echo "  -> Frontend:      http://localhost:3000"
echo "  -> Backend API:   http://localhost:8000"
echo "  -> API Docs:      http://localhost:8000/docs"
echo "  -> Ollama Engine: http://localhost:11434"
echo ""
echo "To view real-time logs, run: docker compose logs -f"
echo "To stop the stack, run:      docker compose down"
