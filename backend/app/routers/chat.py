"""
KavachAI — Chat Router
Multi-turn conversation endpoints with report-grounded and general-purpose AI chat.
Endpoints:
    GET  /conversations           — list conversations
    POST /conversations           — create conversation
    GET  /conversations/{id}      — get conversation with messages
    POST /conversations/{id}/messages — send message & get AI response
    POST /conversations/upload    — upload document/image for chat
    GET  /files/chat/{filename}   — serve uploaded chat files
"""

import os
import uuid
import json
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete

from app.db.database import get_db
from app.db.sql_models import (
    Conversation, ChatMessage, Session as SessionModel, Investigation, Document,
    utcnow,
)
from app.db.object_store import object_store
from app.db.vector_store import vector_store
from app.ingestion.chunk import chunk_pages
from app.ingestion.tag import tag_chunks
from app.ingestion.embed import generate_embeddings
from app.ingestion.extract import extract_text, get_page_count
from app.models.chat import (
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    ChatMessageResponse, SendMessageRequest, AttachmentItem, UploadResponse,
    BatchUploadResponse,
)
from app.orchestrator.model_router import model_router

from app.deps import get_current_session, require_permission
from app.access import assert_owner, owner_filter, validate_attachments
from app.ingestion.limits import read_upload
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["chat"], dependencies=[Depends(require_permission("chat:write"))])

# Upload directory
UPLOAD_DIR = Path("./data/chat_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max messages to include in LLM context
MAX_CONTEXT_MESSAGES = 20

# Allowed file extensions
DOCUMENT_EXTENSIONS = {
    ".pdf", ".txt", ".csv", ".docx", ".text", ".md",
    ".json", ".log", ".tsv", ".yaml", ".yml", ".py", ".sql", ".ini", ".conf",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

# --- System prompts ---

GENERAL_SYSTEM_PROMPT = (
    "You are KavachAI, an intelligent industrial safety and equipment health assistant. "
    "You communicate in clear, easy-to-understand, human-readable plain English so that "
    "any operator, engineer, or manager can immediately learn from and understand your answers. "
    "Avoid unnecessary machine learning jargon or unformatted code dumps. "
    "When explaining architectures, documents, or data, break them down into practical, intuitive steps. "
    "When citing information, reference the source document or data clearly. "
    "If you don't know something, say so honestly."
)


def _build_report_system_prompt(investigation: Investigation) -> str:
    """Build a system prompt grounded in a specific investigation report."""
    report = investigation.report or {}
    findings = report.get("findings", [])

    findings_text = ""
    for i, f in enumerate(findings[:5], 1):
        title = f.get("title", "Untitled")
        detail = f.get("detail", "")
        status = f.get("verification_status", "unknown")
        findings_text += f"\n  {i}. [{status.upper()}] {title}: {detail}"

    return (
        "You are KavachAI, a sovereign industrial AI assistant. "
        "You are answering follow-up questions about a specific investigation report. "
        "Ground ALL your answers in the report evidence below. "
        "If the user asks something not covered by the report, say so.\n\n"
        f"--- INVESTIGATION REPORT ---\n"
        f"Query: {investigation.query}\n"
        f"Status: {report.get('overall_status', investigation.status)}\n"
        f"Condition: {report.get('condition_summary', 'N/A')}\n"
        f"Confidence: {report.get('confidence', investigation.confidence or 'N/A')}%\n"
        f"Verification: {report.get('verification_status', investigation.verification_status or 'N/A')}\n"
        f"Key Findings:{findings_text or ' None'}\n"
        f"Conclusion: {report.get('conclusion', 'N/A')}\n"
        f"--- END REPORT ---"
    )


# ─── List Conversations ─────────────────────────────────────────────

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    type: Optional[str] = Query(None, description="Filter by 'general' or 'report'"),
    investigation_id: Optional[str] = Query(None, description="Filter by investigation ID"),
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """List conversations, optionally filtered by type or investigation_id."""
    query = select(Conversation).where(owner_filter(Conversation, current_session)).order_by(desc(Conversation.updated_at))

    if type:
        query = query.where(Conversation.type == type)
    if investigation_id:
        query = query.where(Conversation.investigation_id == investigation_id)

    result = await db.execute(query)
    conversations = result.scalars().all()

    responses = []
    for conv in conversations:
        # Get last message preview
        last_msg_result = await db.execute(
            select(ChatMessage.content)
            .where(ChatMessage.conversation_id == conv.id)
            .where(ChatMessage.role != "system")
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()

        responses.append(ConversationResponse(
            id=conv.id,
            title=conv.title,
            type=conv.type,
            investigation_id=conv.investigation_id,
            created_at=conv.created_at.isoformat() + "Z",
            updated_at=conv.updated_at.isoformat() + "Z",
            last_message=last_msg[:100] if last_msg else None,
        ))

    return responses


# ─── Create Conversation ─────────────────────────────────────────────

@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """Create a new conversation."""
    session = current_session

    # Validate investigation_id if report type
    if body.type == "report" and body.investigation_id:
        inv_result = await db.execute(
            select(Investigation).where(Investigation.id == body.investigation_id)
        )
        investigation = inv_result.scalar_one_or_none()
        await assert_owner(investigation, current_session, db)

    title = body.title or "New Chat"

    conversation = Conversation(
        session_id=current_session.id,
        user=session.name,
        department=session.department,
        title=title,
        type=body.type,
        investigation_id=body.investigation_id if body.type == "report" else None,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        type=conversation.type,
        investigation_id=conversation.investigation_id,
        created_at=conversation.created_at.isoformat() + "Z",
        updated_at=conversation.updated_at.isoformat() + "Z",
        last_message=None,
    )


# ─── Get Conversation Detail ────────────────────────────────────────

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    await assert_owner(conversation, current_session, db)

    # Fetch messages
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        type=conversation.type,
        investigation_id=conversation.investigation_id,
        created_at=conversation.created_at.isoformat() + "Z",
        updated_at=conversation.updated_at.isoformat() + "Z",
        messages=[
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                attachments=[AttachmentItem(**a) for a in (msg.attachments or [])],
                created_at=msg.created_at.isoformat() + "Z",
            )
            for msg in messages
            if msg.role != "system"  # Don't expose system prompts to client
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    await assert_owner(conversation, current_session, db)

    # Delete all messages in the conversation
    await db.execute(
        delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
    )
    # Delete the conversation record
    await db.delete(conversation)
    await db.commit()
    return Response(status_code=204)


async def _build_grounded_attachment_context(attachments: list, query: str) -> str:
    """
    Intelligently build context from attachments:
    - If total text is concise (<= 6000 chars), inject full contents with file headers.
    - If large or multi-file, query vector_store for top matching passages + file manifest.
    """
    if not attachments:
        return ""

    total_len = 0
    for a in attachments:
        t = getattr(a, "extracted_text", None) if hasattr(a, "extracted_text") else (a.get("extracted_text") if isinstance(a, dict) else None)
        if t:
            total_len += len(t)

    # Strategy A: Short to moderate text across all attachments -> inject entire document text
    if 0 < total_len <= 6000:
        blocks = []
        for a in attachments:
            text = getattr(a, "extracted_text", None) if hasattr(a, "extracted_text") else (a.get("extracted_text") if isinstance(a, dict) else None)
            if text:
                label = getattr(a, "path", None) or getattr(a, "filename", "Document") if hasattr(a, "filename") else (a.get("path") or a.get("filename", "Document"))
                blocks.append(f"=== ATTACHED FILE: {label} ===\n{text}\n=== END OF {label} ===")
        if blocks:
            return "\n\n" + "\n\n".join(blocks)

    # Strategy B: Large documents or folder uploads -> semantic retrieval (RAG) over vector chunks
    source_ids = []
    manifest_names = []
    for a in attachments:
        sid = getattr(a, "source_id", None) if hasattr(a, "source_id") else (a.get("source_id") if isinstance(a, dict) else None)
        fn = getattr(a, "path", None) or getattr(a, "filename", None) if hasattr(a, "filename") else (a.get("path") or a.get("filename"))
        if sid:
            source_ids.append(sid)
        if fn:
            manifest_names.append(fn)

    passages = []
    if source_ids:
        from app.agents import document_agent
        chunks = await document_agent.retrieve(
            sub_task_goal=query,
            filters={"source_ids": source_ids},
            n_results=8,
        )
        for c in chunks:
            passages.append(f"[Excerpt from {c.source_id}, p.{c.page}]:\n{c.chunk_text}")

    if passages:
        manifest_str = ", ".join(manifest_names) if manifest_names else "Uploaded Files"
        return (
            f"\n\n[USER-ATTACHED FILES & FOLDER INVENTORY: {manifest_str}]\n"
            f"Relevant excerpts matching your query from the attached files:\n\n"
            + "\n\n".join(passages)
        )
    elif total_len > 0:
        # Fallback if no vector matches: inject first 2500 chars of each file
        blocks = []
        for a in attachments:
            text = getattr(a, "extracted_text", None) if hasattr(a, "extracted_text") else (a.get("extracted_text") if isinstance(a, dict) else None)
            if text:
                label = getattr(a, "path", None) or getattr(a, "filename", "Document") if hasattr(a, "filename") else (a.get("path") or a.get("filename", "Document"))
                blocks.append(f"=== ATTACHED FILE: {label} (excerpt) ===\n{text[:2500]}\n=== END OF {label} ===")
        return "\n\n" + "\n\n".join(blocks)

    return ""


# ─── Send Message & Get AI Response ─────────────────────────────────

@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """
    Send a user message and get an AI response.
    Builds context from conversation type (general vs report-grounded),
    includes conversation history, grounds on submitted files, and generates via model_router.
    """
    # Load conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    await assert_owner(conversation, current_session, db)

    body.attachments = [AttachmentItem(**a) for a in await validate_attachments(body.attachments, current_session, db)]

    # Build grounded attachment context for user message
    user_content = body.content
    attachment_context = await _build_grounded_attachment_context(body.attachments, body.content)
    if attachment_context:
        user_content = f"{body.content}\n\nEVIDENCE FROM USER-SUBMITTED FILES:{attachment_context}"

    # Save user message
    user_message = ChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=body.content,  # Store original user content
        attachments=[a.model_dump() for a in body.attachments],
    )
    db.add(user_message)

    # Auto-title from first message if still "New Chat"
    if conversation.title == "New Chat" and body.content.strip():
        conversation.title = body.content.strip()[:60]
        if len(body.content.strip()) > 60:
            conversation.title += "…"

    # Build system prompt based on conversation type
    system_prompt = GENERAL_SYSTEM_PROMPT

    if conversation.type == "report" and conversation.investigation_id:
        inv_result = await db.execute(
            select(Investigation).where(
                Investigation.id == conversation.investigation_id
            )
        )
        investigation = inv_result.scalar_one_or_none()
        if investigation and investigation.report:
            system_prompt = _build_report_system_prompt(investigation)

    # Enhance system prompt when user has submitted files
    if body.attachments:
        system_prompt += (
            "\n\nCRITICAL INSTRUCTION: The user has submitted specific files/documents. "
            "You MUST carefully analyze the submitted files provided in the prompt. "
            "Explain the information in clear, human-readable plain English so the user can easily understand and learn from it. "
            "Do not output raw code dumps, infinite loops, or empty placeholder diagrams. "
            "Base your answers, facts, numbers, and recommendations directly on the submitted files, "
            "explaining what each part means in plain, intuitive language."
        )

    # Fetch conversation history (last N messages for context)
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .where(ChatMessage.role != "system")
        .order_by(ChatMessage.created_at)
    )
    history_messages = history_result.scalars().all()

    # Build messages for LLM (system + last N history + current user message)
    llm_messages = [{"role": "system", "content": system_prompt}]

    # Include recent history (skip the user message we just added — it's not committed yet)
    recent_history = history_messages[-(MAX_CONTEXT_MESSAGES - 1):]
    for msg in recent_history:
        content = msg.content
        # Re-inject attachment context for user messages in history if present
        if msg.role == "user" and msg.attachments:
            hist_att_context = await _build_grounded_attachment_context(msg.attachments, msg.content)
            if hist_att_context:
                content = f"{msg.content}\n\nEVIDENCE FROM USER-SUBMITTED FILES:{hist_att_context}"
        llm_messages.append({"role": msg.role, "content": content})

    # Add current user message
    llm_messages.append({"role": "user", "content": user_content})

    # Generate AI response
    try:
        ai_response = await model_router.generate_chat(
            messages=llm_messages,
            task_type="text_reasoning",
            temperature=0.2,
            max_tokens=2048,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(503, "Local inference unavailable") from e

    # Save assistant message
    assistant_message = ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response,
    )
    db.add(assistant_message)

    # Update conversation timestamp
    conversation.updated_at = utcnow()
    await db.commit()
    await db.refresh(assistant_message)

    return ChatMessageResponse(
        id=assistant_message.id,
        role="assistant",
        content=assistant_message.content,
        attachments=[],
        created_at=assistant_message.created_at.isoformat() + "Z",
    )


# ─── File & Folder Upload ─────────────────────────────────────────────

async def _process_chat_file(file, relative_path, db, current_session):
    from app.ingestion.extract import extract_text_with_ocr
    safe_filename = Path((file.filename or "file").replace("\\", "/")).name
    source_id = f"chat_{uuid.uuid4().hex}"
    content = await read_upload(file)
    pages = await extract_text_with_ocr(content, safe_filename)
    if not pages or not any(p.get("text", "").strip() for p in pages):
        raise HTTPException(422, "No readable content extracted; check local OCR/vision availability")
    chunks = tag_chunks(chunk_pages(pages), source_id, safe_filename, "chat_upload", [], current_session.department, current_session.id)
    embeddings = await generate_embeddings([c["text"] for c in chunks])
    object_store.save_raw_file(source_id, content, safe_filename)
    try:
        vector_store.upsert_chunks([f"{source_id}_chunk_{i}" for i in range(len(chunks))],
                                   [c["text"] for c in chunks], embeddings, [c["metadata"] for c in chunks])
        db.add(Document(id=source_id, filename=safe_filename, document_type="chat_upload", status="ready",
                        pages=len(pages), chunks=len(chunks), source_id=source_id,
                        department_scope=current_session.department, session_id=current_session.id))
        await db.commit()
    except Exception:
        await db.rollback()
        vector_store.delete_by_source(source_id)
        object_store.delete(source_id)
        raise
    return UploadResponse(filename=safe_filename, url=f"/api/v1/files/{source_id}/raw",
                          type="image" if Path(safe_filename).suffix.lower() in IMAGE_EXTENSIONS else "document",
                          extracted_text_preview="\n\n".join(p["text"] for p in pages)[:4000],
                          source_id=source_id, path=relative_path, size=len(content), chunk_count=len(chunks))


@router.post("/conversations/upload", response_model=UploadResponse)
async def upload_chat_file(
    file: UploadFile = File(...),
    path: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """
    Upload a single document or image for use in chat.
    Extracts text, indexes into ChromaDB vector store, and registers in DB.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    relative_path = path or file.filename
    return await _process_chat_file(file, relative_path, db, current_session)


@router.post("/conversations/upload-batch", response_model=BatchUploadResponse)
async def upload_chat_batch(
    files: List[UploadFile] = File(...),
    paths: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_session: SessionModel = Depends(get_current_session),
):
    """
    Batch upload multiple files or an entire folder tree for chat.
    Preserves relative paths, extracts text, chunks, embeds into vector DB.
    """
    if len(files) > settings.MAX_BATCH_FILES:
        raise HTTPException(413, "Too many files")
    path_list = []
    if paths:
        try:
            path_list = json.loads(paths)
        except Exception:
            raise HTTPException(422, "paths must be a JSON list")

    uploaded = []
    for idx, file in enumerate(files):
        if not file.filename:
            continue
        rel_path = path_list[idx] if idx < len(path_list) else file.filename
        res = await _process_chat_file(file, rel_path, db, current_session)
        uploaded.append(res)

    return BatchUploadResponse(
        files=uploaded,
        total_files=len(uploaded),
    )


# ─── Serve Uploaded Files ────────────────────────────────────────────

@router.get("/files/chat/{filename}")
async def serve_chat_file(filename: str, current_session: SessionModel = Depends(get_current_session)):
    # Legacy files lack an ownership manifest. They must be reuploaded through authenticated ingestion.
    raise HTTPException(410, "Legacy attachment unavailable; reupload through authenticated ingestion")
