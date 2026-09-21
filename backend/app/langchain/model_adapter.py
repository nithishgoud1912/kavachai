"""
KavachAI — KavachLLM LangChain Adapter

BaseChatModel implementation that routes all LLM calls through ModelRouter
to enforce sovereignty (NFR-SEC-1) and model-swap flexibility (NFR-MNT-2).

Key design decisions:
- Maps ToolMessage → {"role": "tool", "tool_name": m.name} per Ollama native API
- bind_tools() returns a NEW instance (immutable pattern) — doesn't mutate the original
- _agenerate() routes to generate_chat_with_tools() when tools are bound,
  falls back to generate_chat() for plain text conversations
- Factory functions get_reasoning_llm() and get_coding_llm() for easy instantiation
"""

import asyncio
import concurrent.futures
from typing import Any, Dict, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import PrivateAttr

# Map LangChain message types to Ollama role strings
ROLE_MAP = {
    "human": "user",
    "ai": "assistant",
    "system": "system",
    "tool": "tool",
    "user": "user",
    "assistant": "assistant",
}


class KavachLLM(BaseChatModel):
    """
    Sovereign local LLM adapter for LangChain / LangGraph integration.
    Dispatches to ModelRouter with support for native Ollama tool-calling.
    """
    task_type: str = "text_reasoning"
    _tools: list = PrivateAttr(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "kavach-local-ollama"

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
        """Convert LangChain messages to Ollama chat message dictionaries."""
        result = []
        for m in messages:
            role = ROLE_MAP.get(m.type, "user")
            msg: Dict[str, Any] = {"role": role, "content": str(m.content)}

            # AIMessage with tool_calls — forward function call metadata
            if hasattr(m, "tool_calls") and m.tool_calls:
                msg["tool_calls"] = [
                    {"function": {"name": tc["name"], "arguments": tc["args"]}}
                    for tc in m.tool_calls
                ]

            # ToolMessage: must pass tool_name per Ollama native API
            # This is critical for multi-turn tool response association
            if m.type == "tool":
                tool_name = getattr(m, "name", None) or getattr(m, "tool_name", "")
                msg["tool_name"] = tool_name
                msg["name"] = tool_name

            result.append(msg)
        return result

    def _convert_tool_schema(self, lc_tool: Any) -> dict:
        """Convert LangChain BaseTool or schema dictionary to Ollama function tool format."""
        # Handle raw dict schemas (already in Ollama format or partial)
        if isinstance(lc_tool, dict):
            if "type" in lc_tool and "function" in lc_tool:
                return lc_tool
            return {
                "type": "function",
                "function": {
                    "name": lc_tool.get("name", "tool"),
                    "description": lc_tool.get("description", ""),
                    "parameters": lc_tool.get("parameters", {"type": "object", "properties": {}}),
                },
            }

        # Handle LangChain BaseTool instances
        args_schema = getattr(lc_tool, "args_schema", None)
        schema: Dict[str, Any] = {}
        if args_schema:
            if hasattr(args_schema, "model_json_schema"):
                schema = args_schema.model_json_schema()
            elif hasattr(args_schema, "schema"):
                schema = args_schema.schema()

        return {
            "type": "function",
            "function": {
                "name": getattr(lc_tool, "name", str(lc_tool)),
                "description": getattr(lc_tool, "description", "") or "",
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }

    def bind_tools(self, tools: list, **kwargs) -> "KavachLLM":
        """
        Bind tool definitions to the LLM and return a new isolated instance.
        Immutable pattern — the original instance is not mutated.
        """
        bound = KavachLLM(task_type=self.task_type)
        bound._tools = [self._convert_tool_schema(t) for t in tools]
        return bound

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Async generation — the primary code path.
        Routes to generate_chat_with_tools() when tools are bound,
        otherwise falls back to plain generate_chat().
        """
        from app.orchestrator.model_router import model_router

        ollama_messages = self._convert_messages(messages)

        if self._tools:
            # Tool-calling path
            res = await model_router.generate_chat_with_tools(
                messages=ollama_messages,
                tools=self._tools,
                task_type=self.task_type,
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            content = res.get("content", "")
            raw_tool_calls = res.get("tool_calls")
            if raw_tool_calls:
                lc_tool_calls = [
                    {
                        "name": tc.get("function", {}).get("name", ""),
                        "args": tc.get("function", {}).get("arguments", {}),
                        "id": f"call_{tc.get('function', {}).get('name', '')}_{i}",
                    }
                    for i, tc in enumerate(raw_tool_calls)
                ]
                ai_msg = AIMessage(content=content or "", tool_calls=lc_tool_calls)
            else:
                ai_msg = AIMessage(content=content or "")
        else:
            # Plain text path — uses existing generate_chat() -> str
            text = await model_router.generate_chat(
                messages=[{"role": m["role"], "content": m["content"]} for m in ollama_messages],
                task_type=self.task_type,
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            ai_msg = AIMessage(content=text or "")

        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Synchronous wrapper for _agenerate. Handles running event loops safely."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    asyncio.run, self._agenerate(messages, stop=stop, **kwargs)
                ).result()
        else:
            return asyncio.run(self._agenerate(messages, stop=stop, **kwargs))


def get_reasoning_llm() -> KavachLLM:
    """Factory for reasoning tasks (synthesis, planning, verification)."""
    return KavachLLM(task_type="text_reasoning")


def get_coding_llm() -> KavachLLM:
    """Factory for coding / structured tool invocation tasks."""
    return KavachLLM(task_type="coding")
