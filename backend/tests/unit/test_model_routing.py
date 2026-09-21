"""
KavachAI — Unit Tests: LLM Adapter & Model Router Extension
Implements: Person 2 Done Criteria (Tasks 2.1 - 2.5)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from app.orchestrator.model_router import model_router
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


@pytest.mark.asyncio
async def test_generate_chat_returns_string():
    """Verify that existing generate_chat() returns a string (backward compatibility)."""
    with patch.object(model_router, "is_ollama_available", new_callable=AsyncMock) as mock_avail:
        mock_avail.return_value = False
        res = await model_router.generate_chat(
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert isinstance(res, str)


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

    # Test offline / fallback path
    with patch.object(model_router, "is_ollama_available", new_callable=AsyncMock) as mock_avail:
        mock_avail.return_value = False
        res = await model_router.generate_chat_with_tools(
            messages=[{"role": "user", "content": "Investigate P-102"}],
            tools=sample_tools,
        )
        assert isinstance(res, dict)
        assert "content" in res
        assert "tool_calls" in res

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

    # Human
    assert converted[0]["role"] == "user"
    assert converted[0]["content"] == "Run tool"

    # AI with tool_calls
    assert converted[1]["role"] == "assistant"
    assert "tool_calls" in converted[1]
    assert converted[1]["tool_calls"][0]["function"]["name"] == "search_local_documents"

    # ToolMessage
    assert converted[2]["role"] == "tool"
    assert converted[2]["content"] == "Vibration report data"
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
    # Original must not be mutated
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


def test_langchain_prompts():
    """Verify prompt constants exist and are non-empty strings."""
    assert isinstance(INVESTIGATION_SYSTEM_PROMPT, str)
    assert len(INVESTIGATION_SYSTEM_PROMPT) > 20
    assert isinstance(CHAT_SYSTEM_PROMPT, str)
    assert len(CHAT_SYSTEM_PROMPT) > 20
    assert isinstance(DATA_ANALYSIS_PROMPT, str)
    assert len(DATA_ANALYSIS_PROMPT) > 20


def test_kavach_llm_sync_generate():
    """Verify KavachLLM sync invoke() works."""
    llm = KavachLLM(task_type="text_reasoning")
    messages = [HumanMessage(content="Sync prompt")]

    with patch.object(model_router, "generate_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Sync response"
        res = llm.invoke(messages)
        assert res.content == "Sync response"

