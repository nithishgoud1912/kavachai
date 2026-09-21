"""
KavachAI — Unit Tests: Session Ownership, Tool Definitions & LangGraph State
Implements: Person B Done Criteria (Tasks B.1 - B.6)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.runnables import RunnableConfig

from app.db.sql_models import Document, Dataset
from app.ingestion.tag import tag_chunks
from app.agents.document_agent import _build_where_filter
from app.langchain.tools import search_local_documents, analyze_operational_data, ALL_TOOLS
from app.langgraph.state import merge_evidence, InvestigationState
from app.agents.base import DocumentChunk, DataAnalysisResult, TrendDirection, DataPoint


def test_document_model_has_session_id():
    """Verify Document model has nullable session_id column."""
    columns = Document.__table__.columns
    assert "session_id" in columns
    assert columns["session_id"].nullable is True


def test_dataset_model_has_session_id():
    """Verify Dataset model has nullable session_id column."""
    columns = Dataset.__table__.columns
    assert "session_id" in columns
    assert columns["session_id"].nullable is True


def test_tag_chunks_includes_session_id_in_metadata():
    """Verify tag_chunks writes session_id into chunk metadata."""
    chunks = [{"text": "P-102 vibration analysis", "page": 1, "chunk_index": 0}]
    tagged = tag_chunks(
        chunks=chunks,
        source_id="doc_1",
        filename="report.pdf",
        document_type="inspection_report",
        session_id="session_xyz",
    )
    assert len(tagged) == 1
    assert tagged[0]["metadata"]["session_id"] == "session_xyz"


def test_tag_chunks_default_session_id_is_empty():
    """Verify omitting session_id defaults to empty string."""
    chunks = [{"text": "General maintenance note", "page": 1, "chunk_index": 0}]
    tagged = tag_chunks(
        chunks=chunks,
        source_id="doc_2",
        filename="manual.pdf",
        document_type="manual",
    )
    assert len(tagged) == 1
    assert tagged[0]["metadata"]["session_id"] == ""


def test_document_retrieval_filters_by_session():
    """Verify _build_where_filter includes session + shared corpus tokens."""
    f = _build_where_filter({"session_id": "session_abc"})
    assert f == {"session_id": {"$in": ["session_abc", "", "shared", "corpus"]}}

    # Combined with document_types
    f_combo = _build_where_filter({
        "document_types": ["sop"],
        "session_id": "session_abc",
    })
    assert "$and" in f_combo
    conditions = f_combo["$and"]
    assert {"document_type": "sop"} in conditions
    assert {"session_id": {"$in": ["session_abc", "", "shared", "corpus"]}} in conditions


@pytest.mark.asyncio
async def test_tool_search_local_documents_passes_session_id():
    """Verify search_local_documents passes session_id from config to document_agent.retrieve."""
    mock_chunks = [
        DocumentChunk(chunk_text="Vibration normal", source_id="doc_10", page=1, score=0.9),
    ]

    with patch("app.agents.document_agent.retrieve", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = mock_chunks
        config: RunnableConfig = {"configurable": {"session_id": "sess_999"}}

        result = await search_local_documents.ainvoke({"query": "P-102 vibration"}, config=config)

        mock_retrieve.assert_awaited_once_with(
            sub_task_goal="P-102 vibration",
            filters={"session_id": "sess_999"},
            n_results=5,
        )
        assert "[doc_10 p.1]: Vibration normal" in result


@pytest.mark.asyncio
async def test_tool_analyze_operational_data_rejects_unauthorized():
    """Verify analyze_operational_data rejects cross-session / unauthorized datasets."""
    mock_session = MagicMock()
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__.return_value = mock_db

    # Simulate dataset not found / unauthorized
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with patch("app.langchain.tools.async_session", mock_session):
        config: RunnableConfig = {"configurable": {"session_id": "user_sess_1"}}
        res = await analyze_operational_data.ainvoke(
            {"metric": "vibration", "equipment_id": "P-102", "dataset_id": "other_ds"},
            config=config,
        )
        assert "Error: Dataset 'other_ds' not found or unauthorized for this session." in res


@pytest.mark.asyncio
async def test_tool_analyze_operational_data_authorized():
    """Verify analyze_operational_data analyzes data when session owns the dataset."""
    mock_session = MagicMock()
    mock_db = AsyncMock()
    mock_session.return_value.__aenter__.return_value = mock_db

    fake_dataset = MagicMock()
    fake_dataset.id = "valid_ds"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_dataset
    mock_db.execute.return_value = mock_result

    fake_analysis = DataAnalysisResult(
        trend=TrendDirection.INCREASING,
        pct_change=76.2,
        data_points=[DataPoint(timestamp="2026-01-01", equipment_id="P-102", metric="vibration", value=3.7, unit="mm/s")],
        threshold_breach=True,
    )

    with patch("app.langchain.tools.async_session", mock_session), \
         patch("app.agents.data_agent.analyze", return_value=fake_analysis):
        config: RunnableConfig = {"configurable": {"session_id": "user_sess_1"}}
        res = await analyze_operational_data.ainvoke(
            {"metric": "vibration", "equipment_id": "P-102", "dataset_id": "valid_ds"},
            config=config,
        )
        assert "Equipment: P-102, Metric: vibration" in res
        assert "Trend: increasing, Change: +76.2%" in res
        assert "Breached Threshold: True" in res


def test_investigation_state_merge_evidence():
    """Verify merge_evidence reducer combines lists and merges dictionaries."""
    existing = {
        "documents": ["doc_chunk_1"],
        "confidence": 85,
    }
    new = {
        "documents": ["doc_chunk_2"],
        "telemetry": {"trend": "increasing"},
        "confidence": 92,
    }
    merged = merge_evidence(existing, new)
    assert merged["documents"] == ["doc_chunk_1", "doc_chunk_2"]
    assert merged["telemetry"] == {"trend": "increasing"}
    assert merged["confidence"] == 92


def test_investigation_state_merge_evidence_none_handling():
    """Verify merge_evidence handles None safely."""
    assert merge_evidence(None, None) == {}
    assert merge_evidence({"a": 1}, None) == {"a": 1}
    assert merge_evidence(None, {"b": [2]}) == {"b": [2]}


def test_investigation_state_structure():
    """Verify InvestigationState TypedDict defines required fields."""
    annotations = InvestigationState.__annotations__
    required = [
        "investigation_id",
        "session_id",
        "query",
        "attachment_ids",
        "task_type",
        "plan",
        "evidence_bundle",
        "event_log",
        "retry_count",
        "draft_findings",
        "verification_result",
        "deliverables",
    ]
    for field in required:
        assert field in annotations, f"Missing {field} in InvestigationState"


def test_all_tools_exported():
    """Verify ALL_TOOLS contains both search_local_documents and analyze_operational_data."""
    assert len(ALL_TOOLS) == 2
    tool_names = [t.name for t in ALL_TOOLS]
    assert "search_local_documents" in tool_names
    assert "analyze_operational_data" in tool_names
