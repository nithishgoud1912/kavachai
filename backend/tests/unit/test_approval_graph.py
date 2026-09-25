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
    async def test_draft_note_fails_on_source_error(self):
        state = _base_approval_state(draft_version=2)
        with patch(
            "app.services.report_service.render_briefing_draft",
            new_callable=AsyncMock,
            side_effect=Exception("DB error"),
        ):
            with pytest.raises(Exception, match="DB error"):
                await draft_note_node(state)


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
        import uuid
        from app.db.database import init_db, async_session
        from app.db.sql_models import Investigation, SystemSetting
        from pathlib import Path
        from docx import Document
        await init_db()
        id = uuid.uuid4().hex
        async with async_session() as db:
            db.add(Investigation(id=id, session_id='test_session', query='Inspection', status='complete', report={'conclusion':'Original observation','findings':[]}))
            await db.commit()
        state = _base_approval_state(investigation_id=id, draft_version=1,
            officer_edits='Approved with minor edits', draft_note_text='Original draft', reviewer_user_id='reviewer')
        result = await generate_final_node(state)
        assert result['final_docx_url'] == f'/api/v1/exports/{id}/docx'
        async with async_session() as db:
            record = await db.get(SystemSetting, 'approved_export:' + id)
            assert record.value['sha256'] == result['artifact_sha256']
            assert record.value['reviewer_user_id'] == 'reviewer'
            assert Path(record.value['path']).is_file()
            paragraphs = ' '.join(p.text for p in Document(record.value['path']).paragraphs)
            assert 'Approved with minor edits' in paragraphs and 'human approval: approved' in paragraphs

    @pytest.mark.asyncio
    async def test_generate_final_fallback_on_error(self):
        state = _base_approval_state(draft_note_text="Draft")
        with patch(
            "app.services.document_export.generate_briefing_docx",
            new_callable=AsyncMock,
            side_effect=Exception("Export failed"),
        ):
            with pytest.raises(RuntimeError, match="artifact generation failed"):
                await generate_final_node(state)


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
