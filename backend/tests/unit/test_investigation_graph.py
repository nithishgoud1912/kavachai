"""
KavachAI — Unit Tests: Investigation StateGraph
Tests the investigation graph structure, routing, and node behavior.
All tests use mocking to avoid needing live services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.langgraph.state import InvestigationState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _base_state(**overrides) -> InvestigationState:
    """Create a minimal valid InvestigationState for testing."""
    state = {
        "investigation_id": "inv-001",
        "session_id": "sess-001",
        "query": "Investigate vibration increase on pump P-102",
        "attachment_ids": [],
        "task_type": "",
        "selected_models": {},
        "plan": None,
        "evidence_bundle": None,
        "event_log": [],
        "attempt_id": 1,
        "dispatched_agents": [],
        "retry_count": 0,
        "needs_retry": False,
        "retry_reason": None,
        "draft_findings": None,
        "verification_result": None,
        "deliverables": [],
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# State & Reducer Tests
# ---------------------------------------------------------------------------

class TestInvestigationState:
    """Test InvestigationState schema and custom reducers."""

    def test_merge_evidence_empty(self):
        from app.langgraph.state import merge_evidence
        assert merge_evidence(None, None) == {}
        assert merge_evidence(None, {"docs": [1]}) == {"docs": [1]}
        assert merge_evidence({"docs": [1]}, None) == {"docs": [1]}

    def test_merge_evidence_list_concat(self):
        from app.langgraph.state import merge_evidence
        existing = {"documents": [1, 2], "meta": "old"}
        new = {"documents": [3], "meta": "new"}
        result = merge_evidence(existing, new)
        assert result["documents"] == [1, 2, 3]
        assert result["meta"] == "new"

    def test_merge_evidence_preserves_existing_keys(self):
        from app.langgraph.state import merge_evidence
        existing = {"a": "val1", "b": [1]}
        new = {"b": [2], "c": "new"}
        result = merge_evidence(existing, new)
        assert result == {"a": "val1", "b": [1, 2], "c": "new"}


# ---------------------------------------------------------------------------
# Node Tests
# ---------------------------------------------------------------------------

class TestClassifyRequestNode:

    @pytest.mark.asyncio
    async def test_fire_classified_as_emergency(self):
        from app.langgraph.graphs.investigation_graph import classify_request_node
        state = _base_state(query="What is the fire emergency protocol?")
        result = await classify_request_node(state)
        assert result["task_type"] == "emergency_response"
        assert result["attempt_id"] == 1

    @pytest.mark.asyncio
    async def test_pump_classified_as_rca(self):
        from app.langgraph.graphs.investigation_graph import classify_request_node
        state = _base_state(query="Pump P-102 vibration is increasing")
        result = await classify_request_node(state)
        assert result["task_type"] == "root_cause_analysis"

    @pytest.mark.asyncio
    async def test_generic_classified_as_rca(self):
        from app.langgraph.graphs.investigation_graph import classify_request_node
        state = _base_state(query="What are the operational procedures?")
        result = await classify_request_node(state)
        assert result["task_type"] == "root_cause_analysis"


class TestCreatePlanNode:

    @pytest.mark.asyncio
    async def test_always_dispatches_document_agent(self):
        from app.langgraph.graphs.investigation_graph import create_plan_node
        with patch("app.langgraph.graphs.investigation_graph.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            state = _base_state()
            result = await create_plan_node(state)
            assert "gather_documents" in result["dispatched_agents"]

    @pytest.mark.asyncio
    async def test_dispatches_ocr_when_attachments(self):
        from app.langgraph.graphs.investigation_graph import create_plan_node
        with patch("app.langgraph.graphs.investigation_graph.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            state = _base_state(attachment_ids=["att-1", "att-2"])
            result = await create_plan_node(state)
            assert "run_ocr" in result["dispatched_agents"]


class TestValidateEvidenceNode:

    @pytest.mark.asyncio
    async def test_sufficient_when_documents_exist(self):
        from app.langgraph.graphs.investigation_graph import validate_evidence_node
        state = _base_state(evidence_bundle={"documents": [{"chunk_text": "data", "source_id": "s1", "page": 1, "score": 0.9}]})
        result = await validate_evidence_node(state)
        assert result["needs_retry"] is False

    @pytest.mark.asyncio
    async def test_insufficient_when_no_evidence(self):
        from app.langgraph.graphs.investigation_graph import validate_evidence_node
        state = _base_state(evidence_bundle={}, retry_count=0)
        result = await validate_evidence_node(state)
        assert result["needs_retry"] is True
        assert result["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_no_retry_after_max_retries(self):
        from app.langgraph.graphs.investigation_graph import validate_evidence_node
        state = _base_state(evidence_bundle={}, retry_count=2)
        result = await validate_evidence_node(state)
        assert result["needs_retry"] is False


class TestRoutingFunctions:

    def test_check_sufficiency_sufficient(self):
        from app.langgraph.graphs.investigation_graph import check_sufficiency
        state = _base_state(needs_retry=False)
        assert check_sufficiency(state) == "sufficient"

    def test_check_sufficiency_insufficient(self):
        from app.langgraph.graphs.investigation_graph import check_sufficiency
        state = _base_state(needs_retry=True, retry_count=1)
        assert check_sufficiency(state) == "insufficient"

    def test_check_sufficiency_max_retries(self):
        from app.langgraph.graphs.investigation_graph import check_sufficiency
        state = _base_state(needs_retry=True, retry_count=2)
        assert check_sufficiency(state) == "sufficient"

    def test_check_verification_verified(self):
        from app.langgraph.graphs.investigation_graph import check_verification
        state = _base_state(verification_result={"passed": True})
        assert check_verification(state) == "verified"

    def test_check_verification_unverified(self):
        from app.langgraph.graphs.investigation_graph import check_verification
        state = _base_state(verification_result={"passed": False}, retry_count=0)
        assert check_verification(state) == "unverified"

    def test_check_verification_max_retries(self):
        from app.langgraph.graphs.investigation_graph import check_verification
        state = _base_state(verification_result={"passed": False}, retry_count=2)
        assert check_verification(state) == "verified"


class TestDynamicFanOut:

    def test_route_dispatched_agents_creates_sends(self):
        from app.langgraph.graphs.investigation_graph import route_dispatched_agents
        state = _base_state(dispatched_agents=["gather_documents", "analyze_data"])
        sends = route_dispatched_agents(state)
        assert len(sends) == 2
        assert sends[0].node == "gather_documents"
        assert sends[1].node == "analyze_data"

    def test_route_dispatched_agents_empty(self):
        from app.langgraph.graphs.investigation_graph import route_dispatched_agents
        state = _base_state(dispatched_agents=[])
        sends = route_dispatched_agents(state)
        assert len(sends) == 0


class TestGraphStructure:

    def test_graph_compiles(self):
        """Verify the graph compiles without errors using a None checkpointer."""
        from app.langgraph.graphs.investigation_graph import build_investigation_graph
        # Use None checkpointer for structural test (no persistence needed)
        graph = build_investigation_graph(checkpointer=None)
        assert graph is not None
