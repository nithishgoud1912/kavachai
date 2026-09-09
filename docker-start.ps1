# KavachAI Docker Startup Script (PowerShell)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Starting KavachAI Sovereign AI Stack (Docker) " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 1. Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[1/4] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Build and start services
Write-Host "[2/4] Building and launching containers..." -ForegroundColor Green
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker compose failed to start. Ensure Docker Desktop is running." -ForegroundColor Red
    exit 1
}

# 3. Pull required Ollama models if containerized Ollama is used
Write-Host "[3/4] Ensuring Ollama models are pulled..." -ForegroundColor Green
docker compose exec -T ollama ollama pull qwen2.5:3b
docker compose exec -T ollama ollama pull nomic-embed-text

Write-Host "[4/4] All services are up!" -ForegroundColor Cyan
Write-Host ""
Write-Host "  -> Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  -> Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  -> API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  -> Ollama Engine: http://localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "To view real-time logs, run: docker compose logs -f" -ForegroundColor DarkGray
Write-Host "To stop the stack, run: docker compose down" -ForegroundColor DarkGray
