"""Dependency graph builder for schema tables based on foreign-key-like naming."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from sqldiff.schema import Schema


@dataclass
class GraphNode:
    table: str
    depends_on: Set[str] = field(default_factory=set)
    depended_by: Set[str] = field(default_factory=set)

    def __str__(self) -> str:
        return f"GraphNode({self.table}, deps={sorted(self.depends_on)})"


@dataclass
class SchemaGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def tables_in_order(self) -> List[str]:
        """Return tables sorted so dependencies come before dependents (topological)."""
        visited: Set[str] = set()
        result: List[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dep in sorted(self.nodes[name].depends_on):
                if dep in self.nodes:
                    visit(dep)
            result.append(name)

        for table in sorted(self.nodes):
            visit(table)
        return result

    def roots(self) -> List[str]:
        """Tables that nothing else depends on."""
        return [n for n, node in self.nodes.items() if not node.depends_on]

    def leaves(self) -> List[str]:
        """Tables that no other table depends on."""
        return [n for n, node in self.nodes.items() if not node.depended_by]


def build_graph(schema: Schema) -> SchemaGraph:
    """Infer dependencies from columns named <other_table>_id."""
    table_names: Set[str] = set(schema.tables)
    graph = SchemaGraph()

    for name in table_names:
        graph.nodes[name] = GraphNode(table=name)

    for name, table in schema.tables.items():
        for col in table.columns:
            if col.name.endswith("_id"):
                ref = col.name[:-3]  # strip _id
                if ref in table_names and ref != name:
                    graph.nodes[name].depends_on.add(ref)
                    graph.nodes[ref].depended_by.add(name)

    return graph
