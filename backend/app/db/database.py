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
    pass


async def init_db():
    """Create all tables on startup if they don't exist and run column migrations."""
    import app.db.sql_models  # Ensure models are registered with Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def _migrate_columns(sync_conn):
            from sqlalchemy import text
            # Check sessions table
            res = sync_conn.execute(text("PRAGMA table_info(sessions)"))
            columns = [row[1] for row in res.fetchall()]
            if "expires_at" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN expires_at DATETIME"))
            if "is_revoked" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN is_revoked BOOLEAN DEFAULT 0"))
            if "user_id" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN user_id TEXT"))
            if "mfa_verified" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN mfa_verified BOOLEAN DEFAULT 1"))
            if "auth_method" not in columns:
                sync_conn.execute(text("ALTER TABLE sessions ADD COLUMN auth_method TEXT"))

            # Check investigations table
            res_inv = sync_conn.execute(text("PRAGMA table_info(investigations)"))
            inv_cols = [row[1] for row in res_inv.fetchall()]
            if "events" not in inv_cols:
                sync_conn.execute(text("ALTER TABLE investigations ADD COLUMN events JSON DEFAULT '[]'"))
            if "attachments" not in inv_cols:
                sync_conn.execute(text("ALTER TABLE investigations ADD COLUMN attachments JSON DEFAULT '[]'"))

            # Check documents table
            res_doc = sync_conn.execute(text("PRAGMA table_info(documents)"))
            doc_cols = [row[1] for row in res_doc.fetchall()]
            if "session_id" not in doc_cols:
                sync_conn.execute(text("ALTER TABLE documents ADD COLUMN session_id TEXT"))

            # Check datasets table
            res_ds = sync_conn.execute(text("PRAGMA table_info(datasets)"))
            ds_cols = [row[1] for row in res_ds.fetchall()]
            if "session_id" not in ds_cols:
                sync_conn.execute(text("ALTER TABLE datasets ADD COLUMN session_id TEXT"))

        await conn.run_sync(_migrate_columns)


async def get_db() -> AsyncSession:
    """Dependency: yields an async DB session."""
    async with async_session() as session:
        yield session
