"""
KavachAI — NetworkX Graph Store (Equipment Relationships)
Implements: FR-VIS-1/2 (P&ID connectivity), SRS §4.4 (scoped equipment graph)

Pre-loaded with the P-102 demo cluster: T-101 -> P-102 -> V-204 -> R-101
Supports dynamic node/edge addition and cycle-safe graph traversal.
"""

import networkx as nx
from typing import List, Dict, Optional, Any


class GraphStore:
    """In-process equipment relationship graph (NetworkX)."""

    def __init__(self):
        self._graph = nx.DiGraph()
        self._load_demo_graph()

    def _load_demo_graph(self):
        """
        Pre-load the P-102 demo cluster.
        Decision Q11: 4 nodes default — T-101, P-102, V-204, R-101.
        """
        # Nodes with metadata
        self.add_node("T-101", equipment_type="tank", label="Feed Tank T-101")
        self.add_node("P-102", equipment_type="pump", label="Centrifugal Pump P-102")
        self.add_node("V-204", equipment_type="vessel", label="Separation Vessel V-204")
        self.add_node("R-101", equipment_type="reactor", label="Reactor R-101")

        # Edges with relationship labels
        self.add_edge("T-101", "P-102", relationship="feeds_into", label="T-101 feeds into P-102")
        self.add_edge("P-102", "V-204", relationship="discharges_to", label="P-102 discharges to V-204")
        self.add_edge("V-204", "R-101", relationship="feeds_into", label="V-204 feeds into R-101")

    def add_node(self, equipment_id: str, equipment_type: str = "equipment", label: Optional[str] = None) -> None:
        """Add or update an equipment node in the graph."""
        clean_id = equipment_id.strip()
        clean_label = label or f"{equipment_type.capitalize()} {clean_id}"
        self._graph.add_node(clean_id, equipment_type=equipment_type, label=clean_label)

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        relationship: str = "connected_to",
        label: Optional[str] = None,
    ) -> None:
        """Add or update a directed edge connecting two equipment nodes."""
        from_clean = from_id.strip()
        to_clean = to_id.strip()

        # Ensure both nodes exist
        if from_clean not in self._graph:
            self.add_node(from_clean)
        if to_clean not in self._graph:
            self.add_node(to_clean)

        edge_label = label or f"{from_clean} {relationship.replace('_', ' ')} {to_clean}"
        self._graph.add_edge(from_clean, to_clean, relationship=relationship, label=edge_label)

    def get_connections(self, equipment_id: str) -> List[str]:
        """
        Get all directly connected equipment IDs (both upstream and downstream).
        Implements: FR-VIS-2
        """
        if equipment_id not in self._graph:
            return []

        # Get both predecessors and successors without duplicates
        predecessors = list(self._graph.predecessors(equipment_id))
        successors = list(self._graph.successors(equipment_id))

        return list(dict.fromkeys(predecessors + successors))

    def get_connection_chain(self, equipment_id: str) -> List[str]:
        """
        Get the linear chain containing this equipment.
        Guarantees termination even in graphs with feedback loops or cycles.
        """
        if equipment_id not in self._graph:
            return []

        # Find the root / leftmost ancestor avoiding cycles
        current = equipment_id
        visited_backward = {current}
        while True:
            preds = [p for p in self._graph.predecessors(current) if p not in visited_backward]
            if not preds:
                break
            current = preds[0]
            visited_backward.add(current)

        # Walk forward from leftmost node avoiding cycles
        chain = [current]
        visited_forward = {current}
        while True:
            succs = [s for s in self._graph.successors(current) if s not in visited_forward]
            if not succs:
                break
            current = succs[0]
            chain.append(current)
            visited_forward.add(current)

        return chain

    def equipment_exists(self, equipment_id: str) -> bool:
        """Check if an equipment ID exists in the graph."""
        return equipment_id in self._graph

    def get_equipment_info(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an equipment node."""
        if equipment_id not in self._graph:
            return None
        return dict(self._graph.nodes[equipment_id])

    def get_relationship(self, from_id: str, to_id: str) -> Optional[str]:
        """Get the relationship label between two equipment nodes."""
        if self._graph.has_edge(from_id, to_id):
            return self._graph.edges[from_id, to_id].get("relationship", "connected_to")
        return None

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Return all nodes and their attributes."""
        return [
            {"id": node_id, **attrs}
            for node_id, attrs in self._graph.nodes(data=True)
        ]

    def get_all_edges(self) -> List[Dict[str, Any]]:
        """Return all edges and their attributes."""
        return [
            {"from": u, "to": v, **attrs}
            for u, v, attrs in self._graph.edges(data=True)
        ]


# Singleton instance
graph_store = GraphStore()
