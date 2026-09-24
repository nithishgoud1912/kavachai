"""
KavachAI — Unit Tests: LLM Adapter & Model Router Extension
Tests from both Person A (class-based) and Person 2 (function-based).
All tests use mocking to avoid needing a live Ollama server.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from app.orchestrator.model_router import ModelRouter, model_router
from app.langchain.model_adapter import (
    KavachLLM,
    get_reasoning_llm,
    get_coding_llm,
)
from app.langchain.prompts import (
    INVESTIGATION_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    DATA_ANALYSIS_PROMPT,
)


# ===========================================================================
# ModelRouter.generate_chat_with_tools() Tests (Person A — class-based)
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
        with patch.object(router, "is_ollama_available", AsyncMock(return_value=False)):
            with pytest.raises(RuntimeError):
                await router.generate_chat_with_tools(messages=[], tools=[])

    @pytest.mark.asyncio
    async def test_exception_fallback_returns_dict(self, router):
        with patch.object(router, "is_ollama_available", AsyncMock(return_value=True)), patch.object(router._client,"post",AsyncMock(side_effect=RuntimeError("offline"))):
            with pytest.raises(RuntimeError):
                await router.generate_chat_with_tools(messages=[], tools=[])

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
# KavachLLM Adapter Tests (Person A — class-based)
# ===========================================================================


class TestKavachLLM:
    """Tests for the KavachLLM LangChain adapter."""

    def test_llm_type(self):
        llm = KavachLLM()
        assert llm._llm_type == "kavach-local-ollama"

    def test_default_task_type(self):
        llm = KavachLLM()
        assert llm.task_type == "text_reasoning"

    def test_bind_tools_returns_new_instance(self):
        """bind_tools() must return a NEW KavachLLM, not mutate the original."""
        original = KavachLLM(task_type="text_reasoning")
        assert original._tools == []

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

        assert original._tools == []
        assert len(bound._tools) == 1
        assert bound._tools[0]["function"]["name"] == "search_local_documents"
        assert isinstance(bound, KavachLLM)
        assert bound.task_type == "text_reasoning"

    def test_convert_messages_basic(self):
        llm = KavachLLM()
        messages = [
            SystemMessage(content="You are helpful"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
        ]
        result = llm._convert_messages(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"

    def test_convert_tool_message_includes_tool_name(self):
        """ToolMessage must produce tool_name and name keys per Ollama native API."""
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

    def test_convert_ai_message_with_tool_calls(self):
        llm = KavachLLM()
        ai_msg = AIMessage(
            content="",
            tool_calls=[
                {"name": "search_local_documents", "args": {"query": "pump"}, "id": "call_0"}
            ],
        )
        result = llm._convert_messages([ai_msg])

        assert result[0]["tool_calls"][0]["function"]["name"] == "search_local_documents"
        assert result[0]["tool_calls"][0]["function"]["arguments"] == {"query": "pump"}

    def test_convert_tool_schema(self):
        llm = KavachLLM()
        mock_tool = MagicMock()
        mock_tool.name = "analyze_operational_data"
        mock_tool.description = "Analyze telemetry"
        mock_schema = MagicMock(spec=[])  # empty spec so model_json_schema doesn't exist
        mock_schema.schema = MagicMock(return_value={
            "properties": {
                "metric": {"type": "string"},
                "equipment_id": {"type": "string"},
            },
            "required": ["metric", "equipment_id"],
        })
        mock_tool.args_schema = mock_schema

        result = llm._convert_tool_schema(mock_tool)

        assert result["type"] == "function"
        assert result["function"]["name"] == "analyze_operational_data"
        assert "metric" in result["function"]["parameters"]["properties"]


# ===========================================================================
# Person 2 Tests (function-based — from remote)
# ===========================================================================


@pytest.mark.asyncio
async def test_generate_chat_returns_string():
    response=MagicMock()
    response.json.return_value={"message":{"content":"Actual local response"}}
    with patch.object(model_router, "is_ollama_available", AsyncMock(return_value=True)), patch.object(model_router._client,"post",AsyncMock(return_value=response)):
        assert await model_router.generate_chat(messages=[])=="Actual local response"


@pytest.mark.asyncio
async def test_generate_chat_with_tools_returns_dict():
    """Verify generate_chat_with_tools() returns a dict with 'content' and 'tool_calls'."""
    sample_tools = [
        {
            "type": "function",
            "function": {
                "name": "search_docs",
                "description": "search",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]

    with patch.object(model_router, "is_ollama_available", AsyncMock(return_value=False)):
        with pytest.raises(RuntimeError):
            await model_router.generate_chat_with_tools(messages=[], tools=sample_tools)

    # Test online mocked response path
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "content": "Searching...",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_docs",
                        "arguments": {"query": "P-102"},
                    }
                }
            ],
        }
    }
    mock_resp.raise_for_status = MagicMock()

    with patch.object(model_router, "is_ollama_available", new_callable=AsyncMock) as mock_avail, \
         patch.object(model_router._client, "post", new_callable=AsyncMock) as mock_post:
        mock_avail.return_value = True
        mock_post.return_value = mock_resp

        res = await model_router.generate_chat_with_tools(
            messages=[{"role": "user", "content": "Search P-102"}],
            tools=sample_tools,
        )
        assert isinstance(res, dict)
        assert res["content"] == "Searching..."
        assert len(res["tool_calls"]) == 1
        assert res["tool_calls"][0]["function"]["name"] == "search_docs"


def test_kavach_llm_converts_tool_message_with_tool_name():
    """Verify ToolMessage includes tool_name and name keys in converted output."""
    llm = KavachLLM()
    messages = [
        HumanMessage(content="Run tool"),
        AIMessage(
            content="",
            tool_calls=[{"id": "call_1", "name": "search_local_documents", "args": {"query": "vibration"}}],
        ),
        ToolMessage(
            content="Vibration report data",
            tool_call_id="call_1",
            name="search_local_documents",
        ),
    ]
    converted = llm._convert_messages(messages)
    assert len(converted) == 3
    assert converted[0]["role"] == "user"
    assert converted[1]["role"] == "assistant"
    assert "tool_calls" in converted[1]
    assert converted[2]["role"] == "tool"
    assert converted[2]["tool_name"] == "search_local_documents"
    assert converted[2]["name"] == "search_local_documents"


def test_kavach_llm_bind_tools_returns_new_instance():
    """Verify bind_tools() returns a new instance and does not mutate the original."""
    llm = KavachLLM(task_type="text_reasoning")

    @tool
    def dummy_tool(query: str) -> str:
        """A test tool"""
        return query

    bound_llm = llm.bind_tools([dummy_tool])

    assert bound_llm is not llm
    assert isinstance(bound_llm, KavachLLM)
    assert bound_llm.task_type == "text_reasoning"
    assert len(bound_llm._tools) == 1
    assert bound_llm._tools[0]["function"]["name"] == "dummy_tool"
    assert len(llm._tools) == 0


@pytest.mark.asyncio
async def test_kavach_llm_without_tools_uses_generate_chat():
    """Verify KavachLLM without tools delegates to generate_chat()."""
    llm = KavachLLM(task_type="text_reasoning")
    messages = [HumanMessage(content="Hello assistant")]

    with patch.object(model_router, "generate_chat", new_callable=AsyncMock) as mock_chat, \
         patch.object(model_router, "generate_chat_with_tools", new_callable=AsyncMock) as mock_tools:
        mock_chat.return_value = "Hello back"

        result = await llm._agenerate(messages)

        assert mock_chat.await_count == 1
        assert mock_tools.await_count == 0
        assert len(result.generations) == 1
        assert result.generations[0].message.content == "Hello back"


@pytest.mark.asyncio
async def test_kavach_llm_with_tools_parses_tool_calls():
    """Verify KavachLLM with tools delegates to generate_chat_with_tools() and parses tool_calls."""
    llm = KavachLLM(task_type="text_reasoning")

    @tool
    def dummy_tool(query: str) -> str:
        """A test tool"""
        return query

    bound = llm.bind_tools([dummy_tool])
    messages = [HumanMessage(content="Search for P-102")]

    mock_tool_result = {
        "content": "Analyzing...",
        "tool_calls": [
            {
                "function": {
                    "name": "dummy_tool",
                    "arguments": {"query": "P-102"},
                }
            }
        ],
    }

    with patch.object(model_router, "generate_chat", new_callable=AsyncMock) as mock_chat, \
         patch.object(model_router, "generate_chat_with_tools", new_callable=AsyncMock) as mock_tools:
        mock_tools.return_value = mock_tool_result

        result = await bound._agenerate(messages)

        assert mock_tools.await_count == 1
        assert mock_chat.await_count == 0
        msg = result.generations[0].message
        assert isinstance(msg, AIMessage)
        assert msg.content == "Analyzing..."
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["name"] == "dummy_tool"
        assert msg.tool_calls[0]["args"] == {"query": "P-102"}


# ===========================================================================
# Factory Function & Prompt Tests (both persons)
# ===========================================================================


class TestFactoryFunctions:
    def test_get_reasoning_llm(self):
        llm = get_reasoning_llm()
        assert llm.task_type == "text_reasoning"
        assert llm._llm_type == "kavach-local-ollama"

    def test_get_coding_llm(self):
        llm = get_coding_llm()
        assert llm.task_type == "coding"
        assert llm._llm_type == "kavach-local-ollama"


def test_get_reasoning_llm_and_coding_llm():
    """Verify factory functions return properly configured KavachLLM instances."""
    reasoning_llm = get_reasoning_llm()
    assert isinstance(reasoning_llm, KavachLLM)
    assert reasoning_llm.task_type == "text_reasoning"
    assert model_router.get_model("text_reasoning") is not None

    coding_llm = get_coding_llm()
    assert isinstance(coding_llm, KavachLLM)
    assert coding_llm.task_type == "coding"
    assert model_router.get_model("coding") is not None


class TestPrompts:
    def test_investigation_prompt_exists(self):
        assert isinstance(INVESTIGATION_SYSTEM_PROMPT, str)
        assert len(INVESTIGATION_SYSTEM_PROMPT) > 50
        assert "KavachAI" in INVESTIGATION_SYSTEM_PROMPT

    def test_chat_prompt_exists(self):
        assert isinstance(CHAT_SYSTEM_PROMPT, str)
        assert len(CHAT_SYSTEM_PROMPT) > 50
        assert "tools" in CHAT_SYSTEM_PROMPT.lower()

    def test_data_analysis_prompt_exists(self):
        assert isinstance(DATA_ANALYSIS_PROMPT, str)
        assert len(DATA_ANALYSIS_PROMPT) > 50


def test_langchain_prompts():
    """Verify prompt constants exist and are non-empty strings."""
    assert isinstance(INVESTIGATION_SYSTEM_PROMPT, str)
    assert len(INVESTIGATION_SYSTEM_PROMPT) > 20
    assert isinstance(CHAT_SYSTEM_PROMPT, str)
    assert len(CHAT_SYSTEM_PROMPT) > 20
    assert isinstance(DATA_ANALYSIS_PROMPT, str)
    assert len(DATA_ANALYSIS_PROMPT) > 20


# ===========================================================================
# Checkpointer Tests (Person A)
# ===========================================================================


class TestCheckpointer:
    def test_checkpointer_module_imports(self):
        from app.langgraph.checkpointer import init_checkpointer, checkpointer_instance
        assert init_checkpointer is not None
        assert checkpointer_instance is None

    def test_init_checkpointer_is_async_context_manager(self):
        from app.langgraph.checkpointer import init_checkpointer
        cm = init_checkpointer()
        assert hasattr(cm, "__aenter__")
        assert hasattr(cm, "__aexit__")


# ===========================================================================
# Sync invoke test (Person 2)
# ===========================================================================


def test_kavach_llm_sync_generate():
    """Verify KavachLLM sync invoke() works."""
    llm = KavachLLM(task_type="text_reasoning")
    messages = [HumanMessage(content="Sync prompt")]

    with patch.object(model_router, "generate_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Sync response"
        res = llm.invoke(messages)
        assert res.content == "Sync response"
