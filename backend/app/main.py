"""
KavachAI Backend — FastAPI Application Entry Point
Implements: NFR-SEC-2 (local-only CORS), NFR-PERF-3 (SSE streaming support)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — initialize DB on start."""
    await init_db()
    yield


app = FastAPI(
    title="KavachAI",
    description="Sovereign Industrial Agentic AI Workbench — Backend API",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS — only allow the frontend origin (NFR-SEC-2: local-only comms)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check (Phase 0 DoD) ---
@app.get("/health", tags=["system"])
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "service": "kavachai-backend"}


@app.get("/api/v1/health", tags=["system"])
async def api_health_check():
    """API-versioned health check."""
    return {"status": "ok", "service": "kavachai-backend", "version": "0.1.0"}


# --- Route Registration ---
from app.routers import session, knowledge_base, investigations, evidence, export, audit

app.include_router(session.router)
app.include_router(knowledge_base.router)
app.include_router(investigations.router)
app.include_router(evidence.router)
app.include_router(export.router)
app.include_router(audit.router)

