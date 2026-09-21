"""
LangChain @tool definitions for KavachAI agents.
All tools receive session_id via RunnableConfig for data isolation.
Person B owns this file exclusively.
"""
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlalchemy import select, or_
from app.db.database import async_session
from app.db.sql_models import Dataset
from app.agents import document_agent, data_agent


@tool("search_local_documents")
async def search_local_documents(query: str, config: RunnableConfig) -> str:
    """Search organization knowledge base filtered by session."""
    session_id = config.get("configurable", {}).get("session_id")
    chunks = await document_agent.retrieve(
        sub_task_goal=query,
        filters={"session_id": session_id} if session_id else None,
        n_results=5,
    )
    if not chunks:
        return "No relevant documents found in knowledge base."
    return "\n\n".join(f"[{c.source_id} p.{c.page}]: {c.chunk_text[:300]}" for c in chunks)


@tool("analyze_operational_data")
async def analyze_operational_data(
    metric: str, equipment_id: str, dataset_id: str, config: RunnableConfig
) -> str:
    """Run deterministic pandas statistical analysis on a specific dataset."""
    session_id = config.get("configurable", {}).get("session_id")
    # Verify dataset exists and belongs to this session (or is shared)
    async with async_session() as db:
        query = select(Dataset).where(
            Dataset.id == dataset_id,
            or_(Dataset.session_id == session_id, Dataset.session_id.is_(None), Dataset.session_id == "")
        )
        res = await db.execute(query)
        dataset = res.scalar_one_or_none()
        if not dataset:
            return f"Error: Dataset '{dataset_id}' not found or unauthorized for this session."

    result = data_agent.analyze(metric=metric, equipment_id=equipment_id, dataset_id=dataset_id)
    if not result.data_points:
        return f"No telemetry points found for metric '{metric}' on equipment '{equipment_id}'."
    return (
        f"Equipment: {equipment_id}, Metric: {metric}\n"
        f"Trend: {result.trend.value}, Change: {result.pct_change:+.1f}%\n"
        f"Points Sampled: {len(result.data_points)}\n"
        f"Breached Threshold: {result.threshold_breach}"
    )


ALL_TOOLS = [search_local_documents, analyze_operational_data]
