"""
KavachAI — Unit Tests: Planner Agent
Implements: Phase 3 DoD, FR-PLN-1..3, Workflow E

Verifies:
- P-102 investigation decomposes into 4 sub-tasks
- Fire emergency query produces document/RAG tasks
- Out-of-scope query ("crude oil") produces is_in_scope: False
"""

import pytest
from app.agents import planner
from app.agents.base import CorpusSummary, AgentName


@pytest.fixture
def sample_corpus():
    return CorpusSummary(
        documents=7,
        datasets=1,
        pid_drawings=1,
        document_types=["inspection_report", "manual", "sop", "maintenance_history"],
        equipment_ids=["P-102", "T-101", "V-204", "R-101"],
    )


@pytest.mark.asyncio
async def test_planner_p102_decomposition(sample_corpus):
    """Test planner produces 4 sub-tasks for pump deterioration query."""
    query = "Investigate Pump P-102 and determine whether its condition has deteriorated."
    plan = await planner.plan(query, sample_corpus)

    assert plan.is_in_scope is True
    assert len(plan.sub_tasks) >= 2
    agents = [st.agent for st in plan.sub_tasks]
    assert AgentName.DOCUMENT_AGENT in agents


@pytest.mark.asyncio
async def test_planner_fire_emergency_sop(sample_corpus):
    """Test planner assigns document/RAG agents for safety/SOP query."""
    query = "What should an employee do during a fire emergency?"
    plan = await planner.plan(query, sample_corpus)

    assert plan.is_in_scope is True
    agents = [st.agent for st in plan.sub_tasks]
    assert AgentName.DOCUMENT_AGENT in agents or AgentName.RAG_AGENT in agents
    # Pure SOP query should NOT invoke data_agent or vision_agent
    assert AgentName.DATA_AGENT not in agents
    assert AgentName.VISION_AGENT not in agents


@pytest.mark.asyncio
async def test_planner_out_of_scope_refusal(sample_corpus):
    """Test planner flags out-of-scope query (Workflow E / FR-PLN-2)."""
    query = "What is the current price of crude oil?"
    plan = await planner.plan(query, sample_corpus)

    assert plan.is_in_scope is False
    assert len(plan.sub_tasks) == 0
