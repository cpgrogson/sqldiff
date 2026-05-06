"""Tests for sqldiff.loader module."""

import pytest
from pathlib import Path
from sqldiff.loader import load_from_string, load_from_file, load_from_directory


SAMPLE_SQL = """
CREATE TABLE items (
    id INT NOT NULL,
    label VARCHAR(64)
);
"""


def test_load_from_string_basic():
    schema = load_from_string(SAMPLE_SQL)
    assert "items" in schema.tables


def test_load_from_string_type_error():
    with pytest.raises(TypeError):
        load_from_string(123)


def test_load_from_string_empty():
    schema = load_from_string("")
    assert schema.tables == {}


def test_load_from_file(tmp_path):
    sql_file = tmp_path / "schema.sql"
    sql_file.write_text(SAMPLE_SQL, encoding="utf-8")
    schema = load_from_file(sql_file)
    assert "items" in schema.tables


def test_load_from_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_from_file(tmp_path / "nonexistent.sql")


def test_load_from_file_not_a_file(tmp_path):
    with pytest.raises(ValueError):
        load_from_file(tmp_path)


def test_load_from_directory(tmp_path):
    (tmp_path / "a.sql").write_text(
        "CREATE TABLE alpha (id INT NOT NULL);", encoding="utf-8"
    )
    (tmp_path / "b.sql").write_text(
        "CREATE TABLE beta (name VARCHAR(50));", encoding="utf-8"
    )
    schema = load_from_directory(tmp_path)
    assert "alpha" in schema.tables
    assert "beta" in schema.tables


def test_load_from_directory_not_a_dir(tmp_path):
    fake = tmp_path / "notadir"
    with pytest.raises(ValueError):
        load_from_directory(fake)


def test_load_from_directory_empty(tmp_path):
    schema = load_from_directory(tmp_path)
    assert schema.tables == {}


def test_load_from_directory_custom_pattern(tmp_path):
    (tmp_path / "schema.ddl").write_text(
        "CREATE TABLE gamma (val INT);", encoding="utf-8"
    )
    (tmp_path / "other.sql").write_text(
        "CREATE TABLE delta (val INT);", encoding="utf-8"
    )
    schema = load_from_directory(tmp_path, pattern="*.ddl")
    assert "gamma" in schema.tables
    assert "delta" not in schema.tables
