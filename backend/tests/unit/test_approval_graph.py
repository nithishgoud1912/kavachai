"""
KavachAI — Unit Tests: Approval StateGraph
Tests the HITL approval graph structure, node behavior, and routing.
All tests use mocking to avoid needing live DB or services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.langgraph.graphs.approval_graph import (
    ApprovalAction,
    ApprovalState,
    draft_note_node,
    handle_conflict_node,
    generate_final_node,
    route_after_review,
    build_approval_graph,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _base_approval_state(**overrides) -> ApprovalState:
    """Create a minimal valid ApprovalState for testing."""
    state = {
        "investigation_id": "inv-001",
        "session_id": "sess-001",
        "draft_note_text": "",
        "draft_version": 0,
        "approval_status": None,
        "officer_edits": None,
        "final_docx_url": None,
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# State & Enum Tests
# ---------------------------------------------------------------------------

class TestApprovalAction:

    def test_enum_values(self):
        assert ApprovalAction.APPROVED == "approved"
        assert ApprovalAction.REJECTED == "rejected"
        assert ApprovalAction.CONFLICT == "conflict"

    def test_enum_from_string(self):
        assert ApprovalAction("approved") == ApprovalAction.APPROVED
        assert ApprovalAction("rejected") == ApprovalAction.REJECTED
        assert ApprovalAction("conflict") == ApprovalAction.CONFLICT

    def test_invalid_action_raises(self):
        with pytest.raises(ValueError):
            ApprovalAction("invalid_action")


# ---------------------------------------------------------------------------
# Node Tests
# ---------------------------------------------------------------------------

class TestDraftNoteNode:

    @pytest.mark.asyncio
    async def test_draft_note_increments_version(self):
        state = _base_approval_state(draft_version=0)
        with patch(
            "app.services.report_service.render_briefing_draft",
            new_callable=AsyncMock,
            return_value="Draft briefing text"
        ):
            result = await draft_note_node(state)
        assert result["draft_version"] == 1
        assert result["draft_note_text"] == "Draft briefing text"

    @pytest.mark.asyncio
    async def test_draft_note_fallback_on_error(self):
        state = _base_approval_state(draft_version=2)
        with patch(
            "app.services.report_service.render_briefing_draft",
            new_callable=AsyncMock,
            side_effect=Exception("DB error"),
        ):
            result = await draft_note_node(state)
        assert result["draft_version"] == 3
        assert "inv-001" in result["draft_note_text"]


class TestHandleConflictNode:

    @pytest.mark.asyncio
    async def test_conflict_message_includes_version(self):
        state = _base_approval_state(draft_version=3)
        result = await handle_conflict_node(state)
        assert "v3" in result["draft_note_text"]
        assert "CONFLICT" in result["draft_note_text"].upper()


class TestGenerateFinalNode:

    @pytest.mark.asyncio
    async def test_generate_final_with_edits(self):
        state = _base_approval_state(
            officer_edits="Approved with minor edits",
            draft_note_text="Original draft",
        )
        with patch(
            "app.services.document_export.generate_briefing_docx",
            new_callable=AsyncMock,
            return_value="/exports/inv-001/note_for_approval.docx",
        ):
            result = await generate_final_node(state)
        assert result["final_docx_url"] == "/exports/inv-001/note_for_approval.docx"

    @pytest.mark.asyncio
    async def test_generate_final_fallback_on_error(self):
        state = _base_approval_state(draft_note_text="Draft")
        with patch(
            "app.services.document_export.generate_briefing_docx",
            new_callable=AsyncMock,
            side_effect=Exception("Export failed"),
        ):
            result = await generate_final_node(state)
        assert result["final_docx_url"] is None


# ---------------------------------------------------------------------------
# Routing Tests
# ---------------------------------------------------------------------------

class TestRouteAfterReview:

    def test_route_approved(self):
        state = _base_approval_state(approval_status=ApprovalAction.APPROVED)
        assert route_after_review(state) == ApprovalAction.APPROVED

    def test_route_rejected(self):
        state = _base_approval_state(approval_status=ApprovalAction.REJECTED)
        assert route_after_review(state) == ApprovalAction.REJECTED

    def test_route_conflict(self):
        state = _base_approval_state(approval_status=ApprovalAction.CONFLICT)
        assert route_after_review(state) == ApprovalAction.CONFLICT


# ---------------------------------------------------------------------------
# Graph Structure Tests
# ---------------------------------------------------------------------------

class TestApprovalGraphStructure:

    def test_graph_compiles(self):
        """Verify the approval graph compiles without errors."""
        graph = build_approval_graph(checkpointer=None)
        assert graph is not None
