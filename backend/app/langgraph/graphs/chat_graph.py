"""
KavachAI — LangGraph ReAct Multi-Tool Chat Agent
Implements: Phase 4.2 — Compatible with langgraph==0.4.8

Custom ReAct agent implementation that works with the installed langgraph version.
Uses a simple tool-calling loop: LLM decides → tool executes → LLM reasons.
"""

import logging
from typing import TypedDict, Annotated, List, Optional, Any
from operator import add

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

from app.langchain.model_adapter import get_reasoning_llm
from app.langchain.tools import ALL_TOOLS
from app.langchain.prompts import CHAT_SYSTEM_PROMPT

logger = logging.getLogger("kavachai.chat_graph")


class ChatState(TypedDict):
    """State for the ReAct chat agent."""
    messages: Annotated[List[BaseMessage], add]


def _should_continue(state: ChatState) -> str:
    """Check if the last message has tool calls — if so, continue; otherwise end."""
    messages = state.get("messages", [])
    if not messages:
        return "end"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


async def _call_model(state: ChatState) -> dict:
    """Call the LLM with the current message history."""
    llm = get_reasoning_llm()
    bound_llm = llm.bind_tools(ALL_TOOLS)

    # Prepend system message if not already present
    messages = list(state.get("messages", []))
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=CHAT_SYSTEM_PROMPT)] + messages

    response = await bound_llm.ainvoke(messages)
    return {"messages": [response]}


async def _call_tools(state: ChatState) -> dict:
    """Execute tool calls from the last AI message."""
    from langchain_core.messages import ToolMessage

    messages = state.get("messages", [])
    last_message = messages[-1]

    tool_results = []
    tool_map = {t.name: t for t in ALL_TOOLS}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call.get("id", f"call_{tool_name}")

        tool = tool_map.get(tool_name)
        if tool:
            try:
                result = await tool.ainvoke(tool_args)
                tool_results.append(
                    ToolMessage(content=str(result), tool_call_id=tool_id, name=tool_name)
                )
            except Exception as e:
                tool_results.append(
                    ToolMessage(content=f"Error: {e}", tool_call_id=tool_id, name=tool_name)
                )
        else:
            tool_results.append(
                ToolMessage(
                    content=f"Tool '{tool_name}' not found",
                    tool_call_id=tool_id,
                    name=tool_name,
                )
            )

    return {"messages": tool_results}


def build_chat_graph(checkpointer):
    """
    Build and compile the ReAct chat agent graph.

    This is a custom implementation compatible with langgraph==0.4.8 that
    implements the standard ReAct pattern:
      1. Call LLM with messages and bound tools
      2. If LLM returns tool_calls → execute tools → loop back to step 1
      3. If LLM returns text only → end

    Uses:
    - KavachLLM (sovereign local LLM) as the model
    - ALL_TOOLS (search_local_documents, analyze_operational_data)
    - Checkpointer for conversation persistence across requests
    """
    graph = StateGraph(ChatState)

    graph.add_node("agent", _call_model)
    graph.add_node("tools", _call_tools)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue, {
        "tools": "tools",
        "end": END,
    })
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
