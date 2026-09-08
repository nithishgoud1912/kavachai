"""
KavachAI — Planner Agent
Implements: FR-PLN-1 (decompose query into sub-tasks),
            FR-PLN-2 (out-of-scope classification),
            FR-PLN-3 (investigation plan visible to user)

Contract (API_Reference.md §8.1):
    plan(query: str, corpus_summary: CorpusSummary) -> InvestigationPlan

Uses the Model Router for all LLM calls (NFR-MNT-2).
"""

import json
from typing import Optional

from app.agents.base import (
    InvestigationPlan, SubTask, CorpusSummary, AgentName,
)
from app.orchestrator.model_router import model_router


PLANNER_SYSTEM_PROMPT = """You are the Planner Agent for KavachAI, an industrial investigation system.
Your job is to decompose a user's investigation query into sub-tasks for specialist agents.

Available agents and their capabilities:
- document_agent: Searches text documents (inspection reports, maintenance logs, SOPs, manuals). Use for finding specific passages, values, or procedures.
- data_agent: Analyzes structured time-series data (vibration, temperature, pressure readings). Use ONLY when numerical trend analysis is needed.
- vision_agent: Identifies equipment and connections in P&ID drawings. Use ONLY when equipment relationships/connectivity are relevant.
- rag_agent: Retrieves specification thresholds and standards from equipment manuals. Use when comparing actual values against specs/limits.

Rules:
1. Only assign agents that are relevant to the query. A safety/procedural question needs only document_agent and possibly rag_agent.
2. If the query is clearly outside the scope of industrial plant operations (e.g., stock prices, weather, general knowledge), set is_in_scope to false and return empty sub_tasks.
3. Each sub-task must have a clear, specific goal string.
4. Keep sub-tasks focused — one goal per sub-task.

Respond with ONLY valid JSON in this exact format:
{
  "is_in_scope": true/false,
  "sub_tasks": [
    {"agent": "agent_name", "goal": "specific goal description"}
  ]
}"""


async def plan(query: str, corpus_summary: CorpusSummary) -> InvestigationPlan:
    """
    Decompose a user query into an investigation plan.
    Implements: FR-PLN-1, FR-PLN-2, FR-PLN-3

    Args:
        query: the user's natural-language investigation question
        corpus_summary: overview of available documents/datasets/drawings

    Returns:
        InvestigationPlan with sub_tasks and is_in_scope flag
    """
    prompt = f"""Query: "{query}"

Available corpus:
- {corpus_summary.documents} documents (types: {', '.join(corpus_summary.document_types) if corpus_summary.document_types else 'various'})
- {corpus_summary.datasets} structured datasets
- {corpus_summary.pid_drawings} P&ID drawings
- Known equipment: {', '.join(corpus_summary.equipment_ids) if corpus_summary.equipment_ids else 'various'}

Decompose this query into sub-tasks. Respond with JSON only."""

    try:
        response = await model_router.generate(
            prompt=prompt,
            task_type="classification",
            system=PLANNER_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512,
            format="json",
        )

        # Parse JSON response
        plan_data = json.loads(response)

        is_in_scope = plan_data.get("is_in_scope", True)
        sub_tasks = []

        if is_in_scope:
            for st in plan_data.get("sub_tasks", []):
                agent_name = st.get("agent", "")
                # Validate agent name
                try:
                    agent = AgentName(agent_name)
                except ValueError:
                    continue  # Skip unknown agent names

                sub_tasks.append(SubTask(agent=agent, goal=st.get("goal", "")))

        return InvestigationPlan(sub_tasks=sub_tasks, is_in_scope=is_in_scope)

    except json.JSONDecodeError:
        # If LLM returns invalid JSON, try to determine scope from response text
        # Conservative: assume in-scope and create a basic document search task
        return InvestigationPlan(
            sub_tasks=[
                SubTask(agent=AgentName.DOCUMENT_AGENT, goal=f"Search for documents relevant to: {query}"),
                SubTask(agent=AgentName.RAG_AGENT, goal=f"Find specifications related to: {query}"),
            ],
            is_in_scope=True,
        )
    except Exception as e:
        raise RuntimeError(f"Planner failed: {type(e).__name__}: {e}")
