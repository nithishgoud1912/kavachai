"""
KavachAI Backend — SQLAlchemy Database Initialization
Implements: NFR-PORT-1 (SQLite for prototype, swappable to PostgreSQL)
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import os


# Ensure data directory exists
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)

# Async SQLite engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}",
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def init_db():
    """Create all tables on startup and ensure schema evolution."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Auto-migrate newly added columns for SQLite
        def _migrate_columns(sync_conn):
            # Check sessions table
            res = sync_conn.execute(text("PRAGMA table_info(sessions)"))
            columns = [row[1] for row in res.fetchall()]
            if "expires_at" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN expires_at DATETIME"))
            if "is_revoked" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN is_revoked BOOLEAN DEFAULT 0"))

            # Check investigations table
            res_inv = sync_conn.execute(text("PRAGMA table_info(investigations)"))
            inv_cols = [row[1] for row in res_inv.fetchall()]
            if "events" not in inv_cols:
                sync_conn.execute(text("ALTER TABLE investigations ADD COLUMN events JSON DEFAULT '[]'"))

        await conn.run_sync(_migrate_columns)


async def get_db() -> AsyncSession:
    """Dependency: yields an async DB session."""
    async with async_session() as session:
        yield session
