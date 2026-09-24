"""
KavachAI — LangGraph Checkpoint Persistence (Person A — Exclusive File)

Provides AsyncSqliteSaver setup for LangGraph state persistence.
Used as an async context manager in the FastAPI lifespan to ensure
proper setup and teardown of the checkpoint database.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from app.config import settings
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Module-level reference for runtime access outside lifespan
checkpointer_instance: AsyncSqliteSaver | None = None


@asynccontextmanager
async def init_checkpointer():
    """
    Initialize the LangGraph checkpointer with SQLite persistence.

    Usage in FastAPI lifespan:
        async with init_checkpointer() as saver:
            app.state.investigation_graph = build_investigation_graph(saver)
            app.state.approval_graph = build_approval_graph(saver)
            app.state.chat_graph = build_chat_graph(saver)
            yield

    The checkpointer enables:
    - Investigation graph pause/resume across server restarts
    - Human-in-the-loop approval workflow state persistence
    - Chat conversation history with tool call state
    """
    global checkpointer_instance
    async with AsyncSqliteSaver.from_conn_string(str(Path(settings.SQLITE_DB_PATH).resolve().parent / "checkpoints.db")) as saver:
        await saver.setup()  # Ensures checkpoint tables exist
        checkpointer_instance = saver
        yield saver
