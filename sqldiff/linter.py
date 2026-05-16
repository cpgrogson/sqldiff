"""Schema linting: detect common design issues and anti-patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqldiff.schema import Schema, Table


@dataclass
class LintIssue:
    table: str
    column: str | None
    code: str
    message: str
    severity: str  # "warning" | "error"

    def __str__(self) -> str:
        location = self.table
        if self.column:
            location = f"{self.table}.{self.column}"
        return f"[{self.severity.upper()}] {self.code} {location}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def _lint_table(table: Table) -> List[LintIssue]:
    issues: List[LintIssue] = []

    col_names = [c.name.lower() for c in table.columns]

    # L001: no primary key column detected
    pk_hints = {"id", "pk", f"{table.name.lower()}_id"}
    has_pk = any(name in pk_hints for name in col_names)
    if not has_pk:
        issues.append(LintIssue(
            table=table.name,
            column=None,
            code="L001",
            message="No obvious primary key column detected.",
            severity="warning",
        ))

    for col in table.columns:
        # L002: column name contains spaces
        if " " in col.name:
            issues.append(LintIssue(
                table=table.name,
                column=col.name,
                code="L002",
                message="Column name contains spaces.",
                severity="error",
            ))

        # L003: TEXT/BLOB column with a default value (often problematic in MySQL)
        if col.col_type.upper() in ("TEXT", "BLOB") and col.default is not None:
            issues.append(LintIssue(
                table=table.name,
                column=col.name,
                code="L003",
                message=f"Column of type {col.col_type} has a default value, which may not be supported by all databases.",
                severity="warning",
            ))

        # L004: nullable column named with _id suffix (likely FK, should be NOT NULL)
        if col.name.lower().endswith("_id") and col.nullable and col.name.lower() != "id":
            issues.append(LintIssue(
                table=table.name,
                column=col.name,
                code="L004",
                message="Foreign-key-style column is nullable; consider NOT NULL.",
                severity="warning",
            ))

    return issues


def lint_schema(schema: Schema) -> LintResult:
    """Run all lint rules over every table in *schema*.

    Args:
        schema: The :class:`~sqldiff.schema.Schema` instance to inspect.

    Returns:
        A :class:`LintResult` containing all discovered issues.  Call
        ``result.is_clean`` to check whether any issues were found, or iterate
        over ``result.errors`` / ``result.warnings`` to filter by severity.
    """
    result = LintResult()
    for table in schema.tables.values():
        result.issues.extend(_lint_table(table))
    return result
