"""
KavachAI — Chat Pydantic Schemas
Request/response models for multi-turn conversation endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional


class AttachmentItem(BaseModel):
    """A file attachment on a chat message."""
    filename: str
    url: str
    type: str  # "document" | "image"
    extracted_text: Optional[str] = None


class SendMessageRequest(BaseModel):
    """POST /conversations/{id}/messages request body."""
    content: str
    attachments: List[AttachmentItem] = []


class ChatMessageResponse(BaseModel):
    """Single message in a conversation response."""
    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    attachments: List[AttachmentItem] = []
    created_at: str


class ConversationCreate(BaseModel):
    """POST /conversations request body."""
    session_id: str
    title: Optional[str] = None
    type: str = "general"  # "general" | "report"
    investigation_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation list item."""
    id: str
    title: str
    type: str
    investigation_id: Optional[str] = None
    created_at: str
    updated_at: str
    last_message: Optional[str] = None


class ConversationDetailResponse(BaseModel):
    """Full conversation with all messages."""
    id: str
    title: str
    type: str
    investigation_id: Optional[str] = None
    created_at: str
    updated_at: str
    messages: List[ChatMessageResponse]


class UploadResponse(BaseModel):
    """POST /conversations/upload response."""
    filename: str
    url: str
    type: str  # "document" | "image"
    extracted_text_preview: Optional[str] = None
