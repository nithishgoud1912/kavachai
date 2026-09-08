"""
KavachAI — NetworkX Graph Store (Equipment Relationships)
Implements: FR-VIS-1/2 (P&ID connectivity), SRS §4.4 (scoped equipment graph)

Pre-loaded with the P-102 demo cluster: T-101 -> P-102 -> V-204 -> R-101
Vision Agent (Phase 6) reads from this store for the pre-computed fallback approach.
"""

import networkx as nx
from typing import List, Dict, Optional


class GraphStore:
    """In-process equipment relationship graph (NetworkX)."""

    def __init__(self):
        self._graph = nx.DiGraph()
        self._load_demo_graph()

    def _load_demo_graph(self):
        """
        Pre-load the P-102 demo cluster.
        Decision Q11: 4 nodes only — T-101, P-102, V-204, R-101.
        """
        # Nodes with metadata
        self._graph.add_node("T-101", equipment_type="tank", label="Feed Tank T-101")
        self._graph.add_node("P-102", equipment_type="pump", label="Centrifugal Pump P-102")
        self._graph.add_node("V-204", equipment_type="vessel", label="Separation Vessel V-204")
        self._graph.add_node("R-101", equipment_type="reactor", label="Reactor R-101")

        # Edges with relationship labels
        self._graph.add_edge("T-101", "P-102", relationship="feeds_into",
                             label="T-101 feeds into P-102")
        self._graph.add_edge("P-102", "V-204", relationship="discharges_to",
                             label="P-102 discharges to V-204")
        self._graph.add_edge("V-204", "R-101", relationship="feeds_into",
                             label="V-204 feeds into R-101")

    def get_connections(self, equipment_id: str) -> List[str]:
        """
        Get all directly connected equipment IDs (both upstream and downstream).
        Implements: FR-VIS-2

        Returns:
            List of connected equipment IDs
        """
        if equipment_id not in self._graph:
            return []

        # Get both predecessors and successors
        predecessors = list(self._graph.predecessors(equipment_id))
        successors = list(self._graph.successors(equipment_id))

        return predecessors + successors

    def get_connection_chain(self, equipment_id: str) -> List[str]:
        """
        Get the full linear chain containing this equipment.
        For the demo: [T-101, P-102, V-204, R-101]

        Returns:
            Ordered list of equipment IDs in the chain
        """
        if equipment_id not in self._graph:
            return []

        # Find the root (node with no predecessors in this subgraph)
        current = equipment_id
        while True:
            preds = list(self._graph.predecessors(current))
            if not preds:
                break
            current = preds[0]

        # Walk forward from root
        chain = [current]
        while True:
            succs = list(self._graph.successors(current))
            if not succs:
                break
            current = succs[0]
            chain.append(current)

        return chain

    def equipment_exists(self, equipment_id: str) -> bool:
        """Check if an equipment ID exists in the graph."""
        return equipment_id in self._graph

    def get_equipment_info(self, equipment_id: str) -> Optional[Dict]:
        """Get metadata for an equipment node."""
        if equipment_id not in self._graph:
            return None
        return dict(self._graph.nodes[equipment_id])

    def get_relationship(self, from_id: str, to_id: str) -> Optional[str]:
        """Get the relationship label between two equipment nodes."""
        if self._graph.has_edge(from_id, to_id):
            return self._graph.edges[from_id, to_id].get("relationship", "connected_to")
        return None


# Singleton instance
graph_store = GraphStore()
