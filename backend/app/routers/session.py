"""
KavachAI — Session Router
Implements: FR-ACC-1 (capture name + department), FR-ACC-2 (department parameter)
Endpoint: POST /session (API_Reference.md §2)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.sql_models import Session as SessionModel
from app.models.session import SessionCreate, SessionResponse

router = APIRouter(prefix="/api/v1", tags=["session"])


@router.post("/session", response_model=SessionResponse)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a lightweight demo session.
    Implements: FR-ACC-1, FR-ACC-2
    """
    session = SessionModel(name=body.name, department=body.department)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        session_id=session.id,
        name=session.name,
        department=session.department,
        issued_at=session.issued_at.isoformat() + "Z",
    )
