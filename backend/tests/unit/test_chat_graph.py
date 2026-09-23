"""
KavachAI — Unit Tests: ReAct Chat Graph
Tests the chat graph compilation, structure, and configuration.
Uses mocking to avoid needing a live Ollama server.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestChatGraphCompilation:
    """Test that the chat graph compiles and has correct structure."""

    def test_build_chat_graph_compiles(self):
        """Verify the custom ReAct agent graph compiles without errors."""
        from app.langgraph.graphs.chat_graph import build_chat_graph
        graph = build_chat_graph(checkpointer=None)
        assert graph is not None

    def test_chat_graph_has_tools(self):
        """Verify the chat graph binds the expected tools."""
        from app.langchain.tools import ALL_TOOLS
        assert len(ALL_TOOLS) == 2
        tool_names = [t.name for t in ALL_TOOLS]
        assert "search_local_documents" in tool_names
        assert "analyze_operational_data" in tool_names

    def test_chat_graph_uses_kavach_llm(self):
        """Verify the chat graph uses KavachLLM as the model."""
        from app.langchain.model_adapter import KavachLLM, get_reasoning_llm
        llm = get_reasoning_llm()
        assert isinstance(llm, KavachLLM)
        assert llm.task_type == "text_reasoning"
        assert llm._llm_type == "kavach-local-ollama"


class TestChatGraphRouting:
    """Test the routing logic of the chat graph."""

    def test_should_continue_with_tool_calls(self):
        from app.langgraph.graphs.chat_graph import _should_continue
        from langchain_core.messages import AIMessage
        msg = AIMessage(
            content="",
            tool_calls=[{"name": "search_local_documents", "args": {"query": "test"}, "id": "call_1"}],
        )
        state = {"messages": [msg]}
        assert _should_continue(state) == "tools"

    def test_should_continue_without_tool_calls(self):
        from app.langgraph.graphs.chat_graph import _should_continue
        from langchain_core.messages import AIMessage
        msg = AIMessage(content="Here is the answer.")
        state = {"messages": [msg]}
        assert _should_continue(state) == "end"

    def test_should_continue_empty_messages(self):
        from app.langgraph.graphs.chat_graph import _should_continue
        state = {"messages": []}
        assert _should_continue(state) == "end"
