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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.database import get_db
from app.db.sql_models import (
    Conversation, ChatMessage, Session as SessionModel, Investigation,
    utcnow,
)
from app.models.chat import (
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    ChatMessageResponse, SendMessageRequest, AttachmentItem, UploadResponse,
)
from app.orchestrator.model_router import model_router
from app.ingestion.extract import extract_text

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Upload directory
UPLOAD_DIR = Path("./data/chat_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max messages to include in LLM context
MAX_CONTEXT_MESSAGES = 20

# Allowed file extensions
DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".csv", ".docx", ".text", ".md"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# --- System prompts ---

GENERAL_SYSTEM_PROMPT = (
    "You are KavachAI, a sovereign industrial AI assistant specializing in "
    "plant safety, equipment health, maintenance procedures, and engineering "
    "standards. You run entirely on-premise — no data leaves the user's network. "
    "Answer clearly and concisely. When citing information, reference the source "
    "document or data. If you don't know something, say so honestly."
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
):
    """List conversations, optionally filtered by type or investigation_id."""
    query = select(Conversation).order_by(desc(Conversation.updated_at))

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
):
    """Create a new conversation."""
    # Validate session
    session_result = await db.execute(
        select(SessionModel).where(SessionModel.id == body.session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session_id")

    # Validate investigation_id if report type
    if body.type == "report" and body.investigation_id:
        inv_result = await db.execute(
            select(Investigation).where(Investigation.id == body.investigation_id)
        )
        investigation = inv_result.scalar_one_or_none()
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")

    title = body.title or "New Chat"

    conversation = Conversation(
        session_id=body.session_id,
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
):
    """Get a conversation with all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

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


# ─── Send Message & Get AI Response ─────────────────────────────────

@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a user message and get an AI response.
    Builds context from conversation type (general vs report-grounded),
    includes conversation history, and generates via model_router.
    """
    # Load conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Build user content with attachment context
    user_content = body.content
    if body.attachments:
        for att in body.attachments:
            if att.extracted_text:
                user_content += f"\n\n[Attached Document: {att.filename}]\n{att.extracted_text[:2000]}"

    # Save user message
    user_message = ChatMessage(
        conversation_id=conversation_id,
        role="user",
        content=body.content,  # Store original content without injected attachment text
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
        # Re-inject attachment text for user messages in history
        if msg.role == "user" and msg.attachments:
            for att in msg.attachments:
                if att.get("extracted_text"):
                    content += f"\n\n[Attached Document: {att['filename']}]\n{att['extracted_text'][:2000]}"
        llm_messages.append({"role": msg.role, "content": content})

    # Add current user message
    llm_messages.append({"role": "user", "content": user_content})

    # Generate AI response
    try:
        ai_response = await model_router.generate_chat(
            messages=llm_messages,
            task_type="text_reasoning",
            temperature=0.3,
            max_tokens=2048,
        )
    except Exception as e:
        ai_response = (
            "I apologize, but I'm unable to generate a response at this time. "
            "Please ensure the AI backend is running and try again."
        )

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


# ─── File Upload ─────────────────────────────────────────────────────

@router.post("/conversations/upload", response_model=UploadResponse)
async def upload_chat_file(
    file: UploadFile = File(...),
):
    """
    Upload a document or image for use in chat.
    Documents are text-extracted; images are stored as-is.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    is_document = suffix in DOCUMENT_EXTENSIONS
    is_image = suffix in IMAGE_EXTENSIONS

    if not is_document and not is_image:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. "
                   f"Supported: {', '.join(sorted(DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS))}",
        )

    # Generate unique filename to avoid collisions
    unique_name = f"{uuid.uuid4().hex[:12]}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name

    # Read and save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text from documents
    extracted_text_preview = None
    if is_document:
        try:
            pages = extract_text(content, file.filename)
            full_text = "\n".join(p["text"] for p in pages if p.get("text"))
            if full_text:
                extracted_text_preview = full_text[:500]
        except Exception:
            extracted_text_preview = None

    file_url = f"/api/v1/files/chat/{unique_name}"

    return UploadResponse(
        filename=file.filename,
        url=file_url,
        type="document" if is_document else "image",
        extracted_text_preview=extracted_text_preview,
    )


# ─── Serve Uploaded Files ────────────────────────────────────────────

@router.get("/files/chat/{filename}")
async def serve_chat_file(filename: str):
    """Serve an uploaded chat file. Path traversal protection via basename."""
    safe_name = os.path.basename(filename)
    file_path = UPLOAD_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(str(file_path))
