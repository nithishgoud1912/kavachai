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

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

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

router = APIRouter(prefix="/api/v1", tags=["chat"])

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
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

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
            "Base your answers, facts, numbers, and recommendations directly on the submitted files. "
            "Cite the specific file names, sections, and excerpts. If the information is in the files, answer thoroughly."
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


# ─── File & Folder Upload ─────────────────────────────────────────────

async def _process_chat_file(
    file: UploadFile,
    relative_path: str,
    db: AsyncSession,
) -> UploadResponse:
    """Helper to process, save, extract text, chunk, and index a chat upload file."""
    suffix = Path(file.filename).suffix.lower()
    is_document = suffix in DOCUMENT_EXTENSIONS
    is_image = suffix in IMAGE_EXTENSIONS

    if not is_document and not is_image:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. "
                   f"Supported: {', '.join(sorted(DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS))}",
        )

    unique_name = f"{uuid.uuid4().hex[:12]}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name
    source_id = f"chat_{uuid.uuid4().hex[:8]}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Save to object store as well
    object_store.save_raw_file(source_id, content, file.filename)

    extracted_text_preview = None
    chunk_count = 0
    full_text = None

    if is_document:
        try:
            pages = extract_text(content, file.filename)
            page_count = get_page_count(content, file.filename)
            if pages:
                full_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
                if full_text:
                    extracted_text_preview = full_text[:4000] if len(full_text) > 4000 else full_text

                chunks = chunk_pages(pages)
                if chunks:
                    tagged_chunks = tag_chunks(
                        chunks=chunks,
                        source_id=source_id,
                        filename=file.filename,
                        document_type="chat_upload",
                        equipment_ids=[],
                        department_scope=None,
                    )
                    texts = [c["text"] for c in tagged_chunks]
                    embeddings = await generate_embeddings(texts)
                    chunk_ids = [f"{source_id}_chunk_{i}" for i in range(len(tagged_chunks))]
                    metadatas = [c["metadata"] for c in tagged_chunks]
                    for m in metadatas:
                        m["relative_path"] = relative_path

                    vector_store.upsert_chunks(chunk_ids, texts, embeddings, metadatas)
                    chunk_count = len(tagged_chunks)

            # Record in Document table
            doc = Document(
                id=source_id,
                filename=file.filename,
                document_type="chat_upload",
                status="ready",
                pages=page_count if pages else 1,
                chunks=chunk_count,
                equipment_ids=[],
                department_scope=None,
                source_id=source_id,
            )
            db.add(doc)
            await db.commit()
        except Exception:
            pass

    file_url = f"/api/v1/files/chat/{unique_name}"

    return UploadResponse(
        filename=file.filename,
        url=file_url,
        type="document" if is_document else "image",
        extracted_text_preview=extracted_text_preview,
        source_id=source_id,
        path=relative_path,
        size=len(content),
        chunk_count=chunk_count,
    )


@router.post("/conversations/upload", response_model=UploadResponse)
async def upload_chat_file(
    file: UploadFile = File(...),
    path: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a single document or image for use in chat.
    Extracts text, indexes into ChromaDB vector store, and registers in DB.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    relative_path = path or file.filename
    return await _process_chat_file(file, relative_path, db)


@router.post("/conversations/upload-batch", response_model=BatchUploadResponse)
async def upload_chat_batch(
    files: List[UploadFile] = File(...),
    paths: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch upload multiple files or an entire folder tree for chat.
    Preserves relative paths, extracts text, chunks, embeds into vector DB.
    """
    path_list = []
    if paths:
        try:
            path_list = json.loads(paths)
        except Exception:
            path_list = []

    uploaded = []
    for idx, file in enumerate(files):
        if not file.filename:
            continue
        rel_path = path_list[idx] if idx < len(path_list) else file.filename
        res = await _process_chat_file(file, rel_path, db)
        uploaded.append(res)

    return BatchUploadResponse(
        files=uploaded,
        total_files=len(uploaded),
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
