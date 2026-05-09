"""Tests for sqldiff.grapher."""
import pytest

from sqldiff.schema import Column, Schema, Table
from sqldiff.grapher import build_graph, GraphNode, SchemaGraph


def _col(name: str, typ: str = "INTEGER") -> Column:
    return Column(name=name, type=typ, nullable=True, default=None)


def _table(name: str, *col_names: str) -> Table:
    cols = [_col(c) for c in col_names]
    return Table(name=name, columns=cols, indexes=[])


def _schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def test_build_graph_no_fk_columns():
    schema = _schema(
        _table("users", "id", "email"),
        _table("products", "id", "name"),
    )
    graph = build_graph(schema)
    assert set(graph.nodes) == {"users", "products"}
    assert graph.nodes["users"].depends_on == set()
    assert graph.nodes["products"].depends_on == set()


def test_build_graph_detects_fk_column():
    schema = _schema(
        _table("users", "id"),
        _table("orders", "id", "users_id"),
    )
    graph = build_graph(schema)
    assert "users" in graph.nodes["orders"].depends_on
    assert "orders" in graph.nodes["users"].depended_by


def test_build_graph_self_ref_ignored():
    schema = _schema(_table("users", "id", "users_id"))
    graph = build_graph(schema)
    assert graph.nodes["users"].depends_on == set()


def test_build_graph_unknown_ref_ignored():
    schema = _schema(_table("orders", "id", "ghost_id"))
    graph = build_graph(schema)
    assert graph.nodes["orders"].depends_on == set()


def test_tables_in_order_respects_dependency():
    schema = _schema(
        _table("orders", "id", "users_id"),
        _table("users", "id"),
    )
    graph = build_graph(schema)
    order = graph.tables_in_order()
    assert order.index("users") < order.index("orders")


def test_roots_and_leaves():
    schema = _schema(
        _table("users", "id"),
        _table("orders", "id", "users_id"),
        _table("items", "id", "orders_id"),
    )
    graph = build_graph(schema)
    assert "users" in graph.roots()
    assert "items" in graph.leaves()


def test_graph_node_str():
    node = GraphNode(table="orders", depends_on={"users"})
    assert "orders" in str(node)
    assert "users" in str(node)


def test_empty_schema_produces_empty_graph():
    schema = Schema(tables={})
    graph = build_graph(schema)
    assert graph.nodes == {}
    assert graph.tables_in_order() == []
