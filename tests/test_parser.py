"""Tests for sqldiff.parser module."""

import pytest
from sqldiff.parser import parse_sql


SIMPLE_SQL = """
CREATE TABLE users (
    id INT NOT NULL,
    name VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT now
);
"""

MULTI_TABLE_SQL = """
CREATE TABLE orders (
    id INT NOT NULL,
    user_id INT NOT NULL,
    total DECIMAL(10,2),
    INDEX idx_user_id (user_id),
    UNIQUE INDEX idx_total (total)
);

CREATE TABLE products (
    id INT NOT NULL,
    sku VARCHAR(50) NOT NULL,
    price DECIMAL(10,2)
);
"""


def test_parse_single_table():
    schema = parse_sql(SIMPLE_SQL)
    assert "users" in schema.tables
    table = schema.tables["users"]
    assert len(table.columns) == 4


def test_parse_column_names():
    schema = parse_sql(SIMPLE_SQL)
    names = [c.name for c in schema.tables["users"].columns]
    assert names == ["id", "name", "email", "created_at"]


def test_parse_not_null():
    schema = parse_sql(SIMPLE_SQL)
    table = schema.tables["users"]
    assert table.get_column("id").nullable is False
    assert table.get_column("name").nullable is True
    assert table.get_column("email").nullable is False


def test_parse_default():
    schema = parse_sql(SIMPLE_SQL)
    col = schema.tables["users"].get_column("created_at")
    assert col.default == "now"


def test_parse_no_default():
    schema = parse_sql(SIMPLE_SQL)
    col = schema.tables["users"].get_column("id")
    assert col.default is None


def test_parse_multiple_tables():
    schema = parse_sql(MULTI_TABLE_SQL)
    assert "orders" in schema.tables
    assert "products" in schema.tables


def test_parse_indexes():
    schema = parse_sql(MULTI_TABLE_SQL)
    table = schema.tables["orders"]
    assert len(table.indexes) == 2
    idx = table.get_index("idx_user_id")
    assert idx is not None
    assert idx.columns == ["user_id"]
    assert idx.unique is False


def test_parse_unique_index():
    schema = parse_sql(MULTI_TABLE_SQL)
    table = schema.tables["orders"]
    idx = table.get_index("idx_total")
    assert idx is not None
    assert idx.unique is True


def test_parse_empty_sql():
    schema = parse_sql("")
    assert schema.tables == {}


def test_parse_column_type():
    schema = parse_sql(SIMPLE_SQL)
    col = schema.tables["users"].get_column("name")
    assert col.col_type == "VARCHAR(100)"
