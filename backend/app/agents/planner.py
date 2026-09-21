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
- document_agent: Searches text documents (inspection reports, maintenance logs, SOPs, manuals). Use for finding specific passages, historical logs, or procedures.
- data_agent: Analyzes structured time-series data (vibration, temperature, pressure readings). Use whenever numerical trend or telemetry analysis is relevant.
- vision_agent: Analyzes visual P&ID drawings, process schematics, and technical diagrams using multimodal vision (Qwen2.5-VL). Use whenever equipment connectivity, piping topology, inspection drawings, or uploaded engineering PDFs/diagrams are being investigated.
- rag_agent: Retrieves specification thresholds, ISO standards, and limits from manuals. Use when comparing actual values against engineering specs/limits.

Rules:
1. For comprehensive industrial asset investigations (e.g., pumps, heat exchangers, valves, tanks, or specific tags like P-102), schedule all relevant specialist agents (document_agent, data_agent, vision_agent, rag_agent) to ensure a complete multi-perspective forensic analysis.
2. A purely safety or procedural question needs only document_agent and rag_agent.
3. If the query is clearly outside the scope of industrial plant operations (e.g., stock prices, weather, general knowledge), set is_in_scope to false and return empty sub_tasks.
4. If the user provided specific submitted files or folders for this investigation, the query is automatically IN SCOPE (is_in_scope: true). Formulate sub-tasks that specifically analyze the contents of the uploaded files, including vision_agent if drawings or PDFs are attached.
5. Each sub-task must have a clear, specific goal string.

Respond with ONLY valid JSON in this exact format:
{
  "is_in_scope": true/false,
  "sub_tasks": [
    {"agent": "agent_name", "goal": "specific goal description"}
  ]
}"""


async def plan(
    query: str,
    corpus_summary: CorpusSummary,
    attached_files: Optional[list] = None,
) -> InvestigationPlan:
    """
    Decompose a user query into an investigation plan.
    Implements: FR-PLN-1, FR-PLN-2, FR-PLN-3

    Args:
        query: the user's natural-language investigation question
        corpus_summary: overview of available documents/datasets/drawings
        attached_files: optional list of files/folders submitted by the user

    Returns:
        InvestigationPlan with sub_tasks and is_in_scope flag
    """
    attached_info = ""
    if attached_files:
        filenames = [
            f.get("filename") if isinstance(f, dict) else str(f)
            for f in attached_files
        ]
        attached_info = (
            f"\n\nUSER-SUBMITTED FILES FOR THIS INVESTIGATION:\n"
            f"- {len(filenames)} files uploaded: {', '.join(filenames[:10])}\n"
            f"IMPORTANT: The user submitted these documents specifically to be investigated. "
            f"Set is_in_scope to true. If files contain drawings, schematics, or PDFs, assign vision_agent to inspect the visual topology."
        )

    prompt = f"""Query: "{query}"

Available corpus:
- {corpus_summary.documents} documents (types: {', '.join(corpus_summary.document_types) if corpus_summary.document_types else 'various'})
- {corpus_summary.datasets} structured datasets
- {corpus_summary.pid_drawings} P&ID drawings
- Known equipment: {', '.join(corpus_summary.equipment_ids) if corpus_summary.equipment_ids else 'various'}{attached_info}

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
        # If LLM returns invalid JSON, create rich sub-tasks based on query
        import re
        equip_match = re.findall(r"\b([A-Z]-\d{2,4})\b", query)
        equip = equip_match[0] if equip_match else "P-102"

        fallback_tasks = [
            SubTask(agent=AgentName.DOCUMENT_AGENT, goal=f"Search for documents and inspection logs relevant to: {query}"),
            SubTask(agent=AgentName.DATA_AGENT, goal=f"Analyze operational telemetry and trends for {equip}"),
            SubTask(agent=AgentName.VISION_AGENT, goal=f"Visually inspect P&ID process schematic and connectivity for {equip}"),
            SubTask(agent=AgentName.RAG_AGENT, goal=f"Retrieve specifications and operating thresholds for {equip}"),
        ]
        return InvestigationPlan(sub_tasks=fallback_tasks, is_in_scope=True)
    except Exception as e:
        raise RuntimeError(f"Planner failed: {type(e).__name__}: {e}")
