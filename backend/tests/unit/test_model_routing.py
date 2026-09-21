"""
Unit tests for Person A's work:
- ModelRouter.generate_chat_with_tools() — new tool-calling method
- KavachLLM — LangChain adapter with Ollama native tool_name mapping
- Checkpointer — async context manager setup

Tests use mocking to avoid needing a live Ollama server.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.orchestrator.model_router import ModelRouter


# ===========================================================================
# ModelRouter.generate_chat_with_tools() Tests
# ===========================================================================


class TestGenerateChatWithTools:
    """Tests for the new generate_chat_with_tools() method on ModelRouter."""

    @pytest.fixture
    def router(self):
        """Fresh ModelRouter instance."""
        return ModelRouter()

    @pytest.mark.asyncio
    async def test_returns_dict_with_content_and_tool_calls(self, router):
        """generate_chat_with_tools() must return a dict, not a string."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": "I'll search for that.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "search_local_documents",
                            "arguments": {"query": "pump failure"},
                        }
                    }
                ],
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(router, "is_ollama_available", new_callable=AsyncMock, return_value=True):
            with patch.object(router._client, "post", new_callable=AsyncMock, return_value=mock_response):
                result = await router.generate_chat_with_tools(
                    messages=[{"role": "user", "content": "Tell me about pump failures"}],
                    tools=[{"type": "function", "function": {"name": "search_local_documents"}}],
                )

        assert isinstance(result, dict)
        assert "content" in result
        assert "tool_calls" in result
        assert result["content"] == "I'll search for that."
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "search_local_documents"

    @pytest.mark.asyncio
    async def test_returns_none_tool_calls_when_no_tools_invoked(self, router):
        """When the model doesn't call any tools, tool_calls should be None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Here is my answer without tools."}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(router, "is_ollama_available", new_callable=AsyncMock, return_value=True):
            with patch.object(router._client, "post", new_callable=AsyncMock, return_value=mock_response):
                result = await router.generate_chat_with_tools(
                    messages=[{"role": "user", "content": "Hello"}],
                    tools=[{"type": "function", "function": {"name": "search_local_documents"}}],
                )

        assert result["content"] == "Here is my answer without tools."
        assert result["tool_calls"] is None

    @pytest.mark.asyncio
    async def test_offline_fallback_returns_dict(self, router):
        """When Ollama is offline, should still return dict with tool_calls=None."""
        with patch.object(router, "is_ollama_available", new_callable=AsyncMock, return_value=False):
            result = await router.generate_chat_with_tools(
                messages=[{"role": "user", "content": "Tell me about failures"}],
                tools=[{"type": "function", "function": {"name": "search_local_documents"}}],
            )

        assert isinstance(result, dict)
        assert "content" in result
        assert result["tool_calls"] is None
        # Content should be a non-empty fallback string
        assert isinstance(result["content"], str)

    @pytest.mark.asyncio
    async def test_exception_fallback_returns_dict(self, router):
        """Network errors should trigger fallback, returning dict with tool_calls=None."""
        with patch.object(router, "is_ollama_available", new_callable=AsyncMock, return_value=True):
            with patch.object(
                router._client, "post", new_callable=AsyncMock, side_effect=Exception("Connection refused")
            ):
                result = await router.generate_chat_with_tools(
                    messages=[{"role": "user", "content": "Test query"}],
                    tools=[],
                )

        assert isinstance(result, dict)
        assert result["tool_calls"] is None

    @pytest.mark.asyncio
    async def test_sends_tools_in_payload(self, router):
        """The tools list must be included in the Ollama API payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status = MagicMock()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_local_documents",
                    "description": "Search docs",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            }
        ]

        with patch.object(router, "is_ollama_available", new_callable=AsyncMock, return_value=True):
            with patch.object(router._client, "post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
                await router.generate_chat_with_tools(
                    messages=[{"role": "user", "content": "test"}],
                    tools=tools,
                )

        # Verify the payload sent to Ollama includes tools
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "tools" in payload
        assert payload["tools"] == tools

    @pytest.mark.asyncio
    async def test_existing_generate_chat_still_returns_string(self, router):
        """Regression: generate_chat() must still return a plain string."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Plain text response"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(router, "is_ollama_available", new_callable=AsyncMock, return_value=True):
            with patch.object(router._client, "post", new_callable=AsyncMock, return_value=mock_response):
                result = await router.generate_chat(
                    messages=[{"role": "user", "content": "Hello"}],
                )

        assert isinstance(result, str)
        assert result == "Plain text response"


# ===========================================================================
# KavachLLM Adapter Tests
# ===========================================================================


class TestKavachLLM:
    """Tests for the KavachLLM LangChain adapter."""

    def test_llm_type(self):
        """LLM type should identify as kavach-local-ollama."""
        from app.langchain.model_adapter import KavachLLM
        llm = KavachLLM()
        assert llm._llm_type == "kavach-local-ollama"

    def test_default_task_type(self):
        """Default task_type should be text_reasoning."""
        from app.langchain.model_adapter import KavachLLM
        llm = KavachLLM()
        assert llm.task_type == "text_reasoning"

    def test_bind_tools_returns_new_instance(self):
        """bind_tools() must return a NEW KavachLLM, not mutate the original."""
        from app.langchain.model_adapter import KavachLLM

        original = KavachLLM(task_type="text_reasoning")
        assert original._tools == []

        # Create a mock tool with args_schema
        mock_tool = MagicMock()
        mock_tool.name = "search_local_documents"
        mock_tool.description = "Search docs"
        mock_schema = MagicMock()
        mock_schema.schema.return_value = {
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }
        mock_tool.args_schema = mock_schema

        bound = original.bind_tools([mock_tool])

        # Original unchanged
        assert original._tools == []
        # Bound has tools
        assert len(bound._tools) == 1
        assert bound._tools[0]["function"]["name"] == "search_local_documents"
        # Both are KavachLLM
        assert isinstance(bound, KavachLLM)
        # Task type preserved
        assert bound.task_type == "text_reasoning"

    def test_convert_messages_basic(self):
        """Basic message conversion: human -> user, ai -> assistant."""
        from app.langchain.model_adapter import KavachLLM
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        llm = KavachLLM()
        messages = [
            SystemMessage(content="You are helpful"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
        ]

        result = llm._convert_messages(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[0]["content"] == "You are helpful"
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "Hello"
        assert result[2]["role"] == "assistant"
        assert result[2]["content"] == "Hi there"

    def test_convert_tool_message_includes_tool_name(self):
        """ToolMessage must produce tool_name and name keys per Ollama native API."""
        from app.langchain.model_adapter import KavachLLM
        from langchain_core.messages import ToolMessage

        llm = KavachLLM()
        tool_msg = ToolMessage(
            content="Search results: ...",
            name="search_local_documents",
            tool_call_id="call_search_0",
        )

        result = llm._convert_messages([tool_msg])

        assert len(result) == 1
        msg = result[0]
        assert msg["role"] == "tool"
        assert msg["tool_name"] == "search_local_documents"
        assert msg["name"] == "search_local_documents"
        assert msg["content"] == "Search results: ..."

    def test_convert_ai_message_with_tool_calls(self):
        """AIMessage with tool_calls should include function call metadata."""
        from app.langchain.model_adapter import KavachLLM
        from langchain_core.messages import AIMessage

        llm = KavachLLM()
        ai_msg = AIMessage(
            content="",
            tool_calls=[
                {"name": "search_local_documents", "args": {"query": "pump"}, "id": "call_0"}
            ],
        )

        result = llm._convert_messages([ai_msg])

        assert len(result) == 1
        msg = result[0]
        assert msg["role"] == "assistant"
        assert "tool_calls" in msg
        assert msg["tool_calls"][0]["function"]["name"] == "search_local_documents"
        assert msg["tool_calls"][0]["function"]["arguments"] == {"query": "pump"}

    def test_convert_tool_schema(self):
        """Tool schema conversion should produce Ollama function-calling format."""
        from app.langchain.model_adapter import KavachLLM

        llm = KavachLLM()
        mock_tool = MagicMock()
        mock_tool.name = "analyze_operational_data"
        mock_tool.description = "Analyze telemetry"
        mock_schema = MagicMock()
        mock_schema.schema.return_value = {
            "properties": {
                "metric": {"type": "string"},
                "equipment_id": {"type": "string"},
            },
            "required": ["metric", "equipment_id"],
        }
        mock_tool.args_schema = mock_schema

        result = llm._convert_tool_schema(mock_tool)

        assert result["type"] == "function"
        assert result["function"]["name"] == "analyze_operational_data"
        assert result["function"]["description"] == "Analyze telemetry"
        assert "metric" in result["function"]["parameters"]["properties"]
        assert "equipment_id" in result["function"]["parameters"]["required"]


# ===========================================================================
# Factory Function Tests
# ===========================================================================


class TestFactoryFunctions:
    """Tests for get_reasoning_llm() and get_coding_llm()."""

    def test_get_reasoning_llm(self):
        from app.langchain.model_adapter import get_reasoning_llm
        llm = get_reasoning_llm()
        assert llm.task_type == "text_reasoning"
        assert llm._llm_type == "kavach-local-ollama"

    def test_get_coding_llm(self):
        from app.langchain.model_adapter import get_coding_llm
        llm = get_coding_llm()
        assert llm.task_type == "coding"
        assert llm._llm_type == "kavach-local-ollama"


# ===========================================================================
# Prompts Module Tests
# ===========================================================================


class TestPrompts:
    """Tests that prompt constants exist and are non-empty strings."""

    def test_investigation_prompt_exists(self):
        from app.langchain.prompts import INVESTIGATION_SYSTEM_PROMPT
        assert isinstance(INVESTIGATION_SYSTEM_PROMPT, str)
        assert len(INVESTIGATION_SYSTEM_PROMPT) > 50
        assert "KavachAI" in INVESTIGATION_SYSTEM_PROMPT

    def test_chat_prompt_exists(self):
        from app.langchain.prompts import CHAT_SYSTEM_PROMPT
        assert isinstance(CHAT_SYSTEM_PROMPT, str)
        assert len(CHAT_SYSTEM_PROMPT) > 50
        assert "tools" in CHAT_SYSTEM_PROMPT.lower()

    def test_data_analysis_prompt_exists(self):
        from app.langchain.prompts import DATA_ANALYSIS_PROMPT
        assert isinstance(DATA_ANALYSIS_PROMPT, str)
        assert len(DATA_ANALYSIS_PROMPT) > 50


# ===========================================================================
# Checkpointer Tests
# ===========================================================================


class TestCheckpointer:
    """Tests for the LangGraph checkpointer setup."""

    def test_checkpointer_module_imports(self):
        """Verify the checkpointer module can be imported."""
        from app.langgraph.checkpointer import init_checkpointer, checkpointer_instance
        assert init_checkpointer is not None
        # Before init, instance should be None
        assert checkpointer_instance is None

    def test_init_checkpointer_is_async_context_manager(self):
        """init_checkpointer should be usable as an async context manager."""
        import inspect
        from app.langgraph.checkpointer import init_checkpointer
        # It's decorated with @asynccontextmanager, so calling it returns an async CM
        cm = init_checkpointer()
        assert hasattr(cm, "__aenter__")
        assert hasattr(cm, "__aexit__")
