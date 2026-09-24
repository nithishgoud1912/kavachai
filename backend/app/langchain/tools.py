"""
KavachAI — LangChain Tool Definitions
Task 3.4: Session-aware tools for document retrieval and operational data analysis.

Tools:
    search_local_documents   — ChromaDB vector search filtered by session_id
    analyze_operational_data — Deterministic pandas analysis on session-owned datasets
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select, or_
from app.db.database import async_session
from app.db.sql_models import Dataset, Session
from app.access import authorized_sources, assert_owner
from app.agents import document_agent, data_agent


@tool("search_local_documents")
async def search_local_documents(query: str, config: RunnableConfig) -> str:
    """Search organization knowledge base filtered by session.

    Uses vector similarity search against the ChromaDB store. Only documents
    belonging to the current session or the shared corpus are returned.

    Args:
        query: Natural-language search query.
        config: LangChain RunnableConfig carrying `configurable.session_id`.

    Returns:
        Formatted string of matching document chunks with source citations.
    """
    session_id = config.get("configurable", {}).get("session_id")
    async with async_session() as db:
        session = await db.get(Session, session_id) if session_id else None
        sources = await authorized_sources(session, db) if session else []
    chunks = await document_agent.retrieve(
        sub_task_goal=query,
        filters={"source_ids": sources},
        n_results=5,
    )
    if not chunks:
        return "No relevant documents found in knowledge base."
    return "\n\n".join(
        f"[{c.source_id} p.{c.page}]: {c.chunk_text[:300]}" for c in chunks
    )


@tool("analyze_operational_data")
async def analyze_operational_data(
    metric: str, equipment_id: str, dataset_id: str, config: RunnableConfig
) -> str:
    """Run deterministic pandas statistical analysis on a specific dataset.

    Verifies dataset ownership before analysis — only datasets uploaded in the
    current session or shared/null datasets are accessible.

    Args:
        metric:       Metric name to analyse (e.g. "vibration_rms").
        equipment_id: Equipment tag to filter telemetry rows (e.g. "P-102").
        dataset_id:   UUID of the dataset record in the SQL database.
        config:       LangChain RunnableConfig carrying `configurable.session_id`.

    Returns:
        Plain-text analysis summary with trend, percentage change, and threshold
        breach status; or an error string on access violation / missing data.
    """
    session_id = config.get("configurable", {}).get("session_id")

    if not session_id: return "Error: Authenticated session required"
    async with async_session() as db:
        session = await db.get(Session, session_id)
        dataset = await db.get(Dataset, dataset_id)
        if not session or session.is_revoked:
            return "Error: Authenticated session required"
        try:
            await assert_owner(dataset, session, db, shared=True)
        except Exception:
            return f"Error: Dataset '{dataset_id}' not found or unauthorized for this session."

    result = data_agent.analyze(
        metric=metric, equipment_id=equipment_id, dataset_id=dataset_id
    )
    if not result.data_points:
        return (
            f"No telemetry points found for metric '{metric}' on equipment '{equipment_id}'."
        )
    return (
        f"Equipment: {equipment_id}, Metric: {metric}\n"
        f"Trend: {result.trend.value}, Change: {result.pct_change}%\n"
        f"Points Sampled: {len(result.data_points)}\n"
        f"Breached Threshold: {result.threshold_breach}"
    )


# Public export — consumed by LangGraph graph definitions in Phase 3
ALL_TOOLS = [search_local_documents, analyze_operational_data]
