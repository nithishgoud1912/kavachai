"""
KavachAI — Vision/P&ID Agent (Pre-Computed Graph Fallback)
Implements: FR-VIS-1 (locate equipment in P&ID),
            FR-VIS-2 (connectivity list),
            FR-VIS-3 (graceful degradation if not found)

Contract (API_Reference.md §8.4):
    analyze_pid(pid_source_id: str, equipment_id: str)
        -> {found: bool, connections: [str], confidence: float}

Decision Q5: Uses pre-computed NetworkX graph, NOT a live VLM.
The contract is identical — swapping in a real VLM later is zero-change.
"""

from app.agents.base import VisionAnalysisResult
from app.db.graph_store import graph_store


async def analyze_pid(
    pid_source_id: str,
    equipment_id: str,
) -> VisionAnalysisResult:
    """
    Identify equipment and its connections in the P&ID.
    Implements: FR-VIS-1, FR-VIS-2, FR-VIS-3

    Pre-computed fallback: reads from the NetworkX graph store
    instead of running a VLM on the actual P&ID image.

    Args:
        pid_source_id: source_id of the P&ID drawing (acknowledged but not used
                       in the pre-computed fallback — would be used by a live VLM)
        equipment_id: the equipment to find (e.g., "P-102")

    Returns:
        VisionAnalysisResult with found, connections, confidence
    """
    # FR-VIS-1: Check if equipment exists in the graph
    if not graph_store.equipment_exists(equipment_id):
        # FR-VIS-3: Report inability rather than guessing
        return VisionAnalysisResult(
            found=False,
            connections=[],
            confidence=0.0,
        )

    # FR-VIS-2: Get connectivity list
    connections = graph_store.get_connections(equipment_id)

    # Pre-computed graph: confidence is high (it's deterministic)
    return VisionAnalysisResult(
        found=True,
        connections=connections,
        confidence=0.95,  # High confidence for pre-computed data
    )


async def get_connection_chain(equipment_id: str) -> list[str]:
    """
    Get the full linear chain containing this equipment.
    Used for the pid_relationship field in the report.

    Returns:
        e.g., ["T-101", "P-102", "V-204", "R-101"]
    """
    return graph_store.get_connection_chain(equipment_id)
