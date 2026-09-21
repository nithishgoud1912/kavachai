"""
KavachAI — Unit Tests: Session Ownership, Tool Definitions & LangGraph State
Implements: Person B / Person 3 Done Criteria
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.runnables import RunnableConfig
from sqlalchemy import inspect as sa_inspect

from app.db.sql_models import Document, Dataset
from app.ingestion.tag import tag_chunks
from app.agents import document_agent
from app.agents.document_agent import _build_where_filter
from app.langchain.tools import search_local_documents, analyze_operational_data, ALL_TOOLS
from app.langgraph.state import merge_evidence, InvestigationState
from app.agents.base import DocumentChunk, DataAnalysisResult, TrendDirection, DataPoint


# ---------------------------------------------------------------------------
# Task 3.1 / B.1 — DB model column tests
# ---------------------------------------------------------------------------

class TestDatabaseModels:
    """Verify that session_id columns were added correctly."""

    def test_document_model_has_session_id(self):
        """Document.session_id column exists and is nullable."""
        mapper = sa_inspect(Document)
        col = mapper.c.get("session_id")
        assert col is not None, "Document.session_id column is missing"
        assert col.nullable is True, "Document.session_id must be nullable"

    def test_dataset_model_has_session_id(self):
        """Dataset.session_id column exists and is nullable."""
        mapper = sa_inspect(Dataset)
        col = mapper.c.get("session_id")
        assert col is not None, "Dataset.session_id column is missing"
        assert col.nullable is True, "Dataset.session_id must be nullable"

    def test_document_session_id_has_foreign_key(self):
        """Document.session_id has a FK pointing at sessions.id."""
        mapper = sa_inspect(Document)
        col = mapper.c.get("session_id")
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "sessions.id" in fk_targets, (
            f"Document.session_id FK should point to sessions.id, got {fk_targets}"
        )

    def test_dataset_session_id_has_foreign_key(self):
        """Dataset.session_id has a FK pointing at sessions.id."""
        mapper = sa_inspect(Dataset)
        col = mapper.c.get("session_id")
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "sessions.id" in fk_targets, (
            f"Dataset.session_id FK should point to sessions.id, got {fk_targets}"
        )


# ---------------------------------------------------------------------------
# Task 3.2 / B.2 — tag_chunks session_id tests
# ---------------------------------------------------------------------------

SAMPLE_CHUNKS = [
    {"text": "Pump P-102 inspection passed.", "page": 1, "chunk_index": 0},
    {"text": "Valve V-301 showing wear.", "page": 2, "chunk_index": 1},
]


class TestTagChunks:
    """Verify session_id is written into ChromaDB metadata."""

    def test_tag_chunks_includes_session_id_in_metadata(self):
        """Tagged chunks contain 'session_id' key when supplied."""
        tagged = tag_chunks(
            chunks=SAMPLE_CHUNKS,
            source_id="doc-abc",
            filename="report.pdf",
            document_type="inspection_report",
            session_id="sess-xyz",
        )
        for chunk in tagged:
            assert "session_id" in chunk["metadata"], (
                "session_id key missing from tagged chunk metadata"
            )
            assert chunk["metadata"]["session_id"] == "sess-xyz", (
                f"Expected 'sess-xyz', got '{chunk['metadata']['session_id']}'"
            )

    def test_tag_chunks_default_session_id_is_empty(self):
        """Omitting session_id defaults to empty string in metadata."""
        tagged = tag_chunks(
            chunks=SAMPLE_CHUNKS,
            source_id="doc-abc",
            filename="report.pdf",
            document_type="inspection_report",
        )
        for chunk in tagged:
            assert chunk["metadata"]["session_id"] == "", (
                "Default session_id should be empty string, not None or missing"
            )

    def test_tag_chunks_explicit_none_session_id_is_empty(self):
        """Passing session_id=None still produces empty string in metadata."""
        tagged = tag_chunks(
            chunks=SAMPLE_CHUNKS,
            source_id="doc-abc",
            filename="report.pdf",
            document_type="inspection_report",
            session_id=None,
        )
        for chunk in tagged:
            assert chunk["metadata"]["session_id"] == ""

    def test_tag_chunks_preserves_existing_metadata(self):
        """Adding session_id does not remove other metadata fields."""
        tagged = tag_chunks(
            chunks=SAMPLE_CHUNKS,
            source_id="doc-abc",
            filename="report.pdf",
            document_type="sop",
            department_scope="engineering",
            session_id="sess-xyz",
        )
        required_keys = {
            "source_id", "filename", "page", "chunk_index",
            "document_type", "equipment_ids", "department_scope", "session_id",
        }
        for chunk in tagged:
            assert required_keys.issubset(chunk["metadata"].keys()), (
                f"Missing metadata keys: {required_keys - chunk['metadata'].keys()}"
            )


# ---------------------------------------------------------------------------
# Task 3.3 / B.3 — document_agent session filtering tests
# ---------------------------------------------------------------------------

class TestDocumentRetrievalSessionFilter:
    """Verify _build_where_filter handles session_id correctly."""

    def test_session_id_filter_builds_in_clause(self):
        """session_id filter includes session + shared/corpus values."""
        where = document_agent._build_where_filter({"session_id": "sess-xyz"})
        assert where is not None
        in_values = where.get("session_id", {}).get("$in", [])
        assert "sess-xyz" in in_values, "Session ID missing from $in list"
        assert "" in in_values, "Empty string (corpus) missing from $in list"
        assert "shared" in in_values, "'shared' sentinel missing from $in list"
        assert "corpus" in in_values, "'corpus' sentinel missing from $in list"

    def test_empty_session_id_is_ignored(self):
        """Falsy session_id (empty string) is NOT added to filter conditions."""
        where = document_agent._build_where_filter({"session_id": ""})
        assert where is None, (
            "Empty session_id should produce no filter (None), not apply a condition"
        )

    def test_session_id_combined_with_department_scope(self):
        """session_id and department_scope produce a combined $and filter."""
        where = document_agent._build_where_filter({
            "session_id": "sess-xyz",
            "department_scope": "engineering",
        })
        assert "$and" in where, "Combined filters should use $and operator"
        keys_in_and = {list(c.keys())[0] for c in where["$and"]}
        assert "session_id" in keys_in_and
        assert "department_scope" in keys_in_and

    @pytest.mark.asyncio
    async def test_document_retrieval_filters_by_session(self):
        """retrieve() passes session_id through to _build_where_filter."""
        mock_embedding = [0.1] * 768
        mock_results = [
            {
                "chunk_text": "Test chunk",
                "source_id": "doc-abc",
                "page": 1,
                "score": 0.9,
                "metadata": {"session_id": "sess-xyz", "equipment_ids": ""},
            }
        ]

        with (
            patch(
                "app.agents.document_agent.model_router.embed",
                new=AsyncMock(return_value=[mock_embedding]),
            ),
            patch(
                "app.agents.document_agent.vector_store.query",
                return_value=mock_results,
            ),
            patch(
                "app.agents.document_agent._build_where_filter",
                wraps=document_agent._build_where_filter,
            ) as mock_filter,
        ):
            await document_agent.retrieve(
                sub_task_goal="pump failure cause",
                filters={"session_id": "sess-xyz"},
                n_results=3,
            )
            mock_filter.assert_called_once_with({"session_id": "sess-xyz"})


# ---------------------------------------------------------------------------
# Task 3.4 / B.4 — Tool tests
# ---------------------------------------------------------------------------

class TestToolDatasetOwnership:
    """Verify tool execution and dataset ownership validation."""

    @pytest.mark.asyncio
    async def test_tool_search_local_documents_passes_session_id(self):
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
    async def test_tool_validates_dataset_ownership_rejects_cross_session(self):
        """Tool returns error when dataset belongs to a different session."""
        mock_config = {"configurable": {"session_id": "sess-current"}}

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        with patch("app.langchain.tools.async_session", return_value=mock_db):
            result = await analyze_operational_data.ainvoke(
                {
                    "metric": "vibration_rms",
                    "equipment_id": "P-102",
                    "dataset_id": "dataset-other-session",
                    "config": mock_config,
                }
            )

        assert "not found or unauthorized" in result, (
            f"Expected unauthorized error message, got: {result!r}"
        )

    @pytest.mark.asyncio
    async def test_tool_validates_dataset_ownership_allows_shared(self):
        """Tool proceeds when dataset has no session_id (shared corpus)."""
        mock_config = {"configurable": {"session_id": "sess-current"}}

        mock_dataset = MagicMock(spec=Dataset)
        mock_dataset.id = "dataset-shared"
        mock_dataset.session_id = None

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = mock_dataset
        mock_db.execute = AsyncMock(return_value=mock_execute_result)

        mock_analysis = MagicMock()
        mock_analysis.data_points = [1, 2, 3]
        mock_analysis.trend.value = "increasing"
        mock_analysis.pct_change = 12.5
        mock_analysis.threshold_breach = False

        with (
            patch("app.langchain.tools.async_session", return_value=mock_db),
            patch("app.langchain.tools.data_agent.analyze", return_value=mock_analysis),
        ):
            result = await analyze_operational_data.ainvoke(
                {
                    "metric": "vibration_rms",
                    "equipment_id": "P-102",
                    "dataset_id": "dataset-shared",
                    "config": mock_config,
                }
            )

        assert "Trend: increasing" in result, (
            f"Expected analysis output, got: {result!r}"
        )
        assert "Change: +12.5%" in result

    def test_all_tools_exported(self):
        """Verify ALL_TOOLS contains both search_local_documents and analyze_operational_data."""
        assert len(ALL_TOOLS) == 2
        tool_names = [t.name for t in ALL_TOOLS]
        assert "search_local_documents" in tool_names
        assert "analyze_operational_data" in tool_names


# ---------------------------------------------------------------------------
# Task B.5 — LangGraph State tests
# ---------------------------------------------------------------------------

class TestLangGraphState:
    """Verify LangGraph state and evidence reducer."""

    def test_investigation_state_merge_evidence(self):
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

    def test_investigation_state_merge_evidence_none_handling(self):
        """Verify merge_evidence handles None safely."""
        assert merge_evidence(None, None) == {}
        assert merge_evidence({"a": 1}, None) == {"a": 1}
        assert merge_evidence(None, {"b": [2]}) == {"b": [2]}

    def test_investigation_state_structure(self):
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
