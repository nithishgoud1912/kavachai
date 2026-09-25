"""Resource policy shared by routes and retrieval. Ownership follows users across logins."""
from fastapi import HTTPException
from sqlalchemy import select, or_
from app.db.sql_models import Session, Document
from app.security import can_access_classification


def owned_sessions(session: Session):
    if session.user_id:
        return select(Session.id).where(Session.user_id == session.user_id)
    return select(Session.id).where(Session.id == session.id)


def owner_filter(model, session: Session, shared=False):
    owner = model.session_id.in_(owned_sessions(session))
    return or_(owner, model.session_id.is_(None)) if shared else owner


async def assert_owner(resource, session, db, shared=False):
    if resource is None:
        raise HTTPException(404, "Resource not found")
    owner_id = getattr(resource, "session_id", None)
    allowed = owner_id is None and shared
    if owner_id:
        allowed = owner_id in (await db.execute(owned_sessions(session))).scalars().all()
    if not allowed:
        raise HTTPException(404, "Resource not found")
    department = getattr(resource, "department_scope", None)
    if department and department.casefold() != session.department.casefold():
        raise HTTPException(404, "Resource not found")
    if session.user_id:
        from app.db.sql_models import User
        user = await db.get(User, session.user_id)
        if not user or not can_access_classification(user.clearance, getattr(resource, "classification", "internal")):
            raise HTTPException(403, "Insufficient clearance")


async def authorized_sources(session, db):
    docs = (await db.execute(select(Document).where(owner_filter(Document, session, shared=True)))).scalars().all()
    sources = []
    for doc in docs:
        try:
            await assert_owner(doc, session, db, shared=True)
            sources.append(doc.source_id)
        except HTTPException:
            continue
    return sources


async def validate_attachments(attachments, session, db):
    """Ignore client-supplied evidence text; reconstruct it from authorized stored files."""
    from app.db.object_store import object_store
    from app.ingestion.extract import extract_text_with_ocr
    result = []
    for attachment in attachments:
        item = attachment.model_dump() if hasattr(attachment, "model_dump") else dict(attachment)
        source = item.get("source_id")
        fname = item.get("filename", "unnamed file")
        if not source:
            raise HTTPException(400, f"Attachment '{fname}' has not been uploaded to the local repository yet or is missing a valid source_id.")
        doc = (await db.execute(select(Document).where(Document.source_id == source))).scalar_one_or_none()
        if not doc:
            raise HTTPException(404, f"Attachment '{fname}' (source_id: {source}) was not found in the authorized document repository.")
        await assert_owner(doc, session, db, shared=True)
        raw = object_store.get_raw_file(source)
        if not raw:
            raise HTTPException(404, f"Attachment file data for '{fname}' is unavailable")
        pages = await extract_text_with_ocr(*raw)
        item.update(filename=doc.filename, url=f"/api/v1/files/{source}/raw",
                    extracted_text="\n\n".join(p['text'] for p in pages)[:100000])
        result.append(item)
    return result
