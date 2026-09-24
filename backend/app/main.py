"""
KavachAI Backend — FastAPI Application Entry Point
Implements: NFR-SEC-2 (local-only CORS), NFR-PERF-3 (SSE streaming support)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db
from app.middleware.egress_monitor import egress_monitor
from app.langgraph.checkpointer import init_checkpointer
from app.langgraph.graphs.investigation_graph import build_investigation_graph
from app.langgraph.graphs.approval_graph import build_approval_graph
from app.langgraph.graphs.chat_graph import build_chat_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — initialize DB, egress audit, LangGraph on start."""
    if settings.ENVIRONMENT == "production" and settings.ALLOW_DEMO_SESSIONS:
        raise RuntimeError("Production cannot enable unauthenticated demo sessions")
    # 1. Existing DB init preserved
    await init_db()

    # Interrupted jobs are explicitly failed, never silently left running.
    from app.db.database import async_session
    from app.db.sql_models import WorkbenchJob, Investigation
    from sqlalchemy import select
    async with async_session() as db:
        for job in (await db.execute(select(WorkbenchJob).where(WorkbenchJob.status.in_(["queued", "running"])))).scalars():
            job.status = "failed"
            job.payload = {**job.payload, "status":"failed", "error":"Server restarted; resubmit task"}
            job.events = [*(job.events or []), {"type":"task_failed", "data":{"task_id":job.id, "error":"Server restarted"}}]
        for inv in (await db.execute(select(Investigation).where(Investigation.status.in_(["planning", "investigating"])))).scalars():
            inv.status = "failed"
        await db.commit()

    from app.db.sql_models import SystemSetting
    from app.orchestrator.model_router import model_router
    async with async_session() as db:
        routing = await db.get(SystemSetting, "routing")
        if routing:
            model_router._model_map.update({k:v for k,v in routing.value.items() if k in model_router._model_map and k != "embedding"})
    # 2. Egress monitor — sovereignty proof via socket audit
    egress_monitor.install_socket_audit()

    # 3. Checkpointer initialization & Graph compilation
    async with init_checkpointer() as checkpointer:
        app.state.approval_graph = build_approval_graph(checkpointer)
        yield
    await model_router.close()


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
from app.routers import session, knowledge_base, investigations, evidence, export, audit, chat, approval, auth, exports

app.include_router(session.router)
app.include_router(auth.router)
app.include_router(knowledge_base.router)
app.include_router(investigations.router)
app.include_router(evidence.router)
app.include_router(export.router)
app.include_router(audit.router)
app.include_router(chat.router)
app.include_router(approval.router)



app.include_router(exports.router)

from app.routers import workbench
app.include_router(workbench.router)

from app.routers import runtime
app.include_router(runtime.router)
