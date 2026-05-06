"""Schema validation utilities for sqldiff."""

from dataclasses import dataclass, field
from typing import List

from sqldiff.schema import Schema, Table


@dataclass
class ValidationIssue:
    table: str
    message: str
    severity: str = "warning"  # "warning" or "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.table}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def __len__(self) -> int:
        return len(self.issues)


def _validate_table(table: Table) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if not table.columns:
        issues.append(ValidationIssue(
            table=table.name,
            message="Table has no columns.",
            severity="error",
        ))

    col_names = [c.name for c in table.columns]
    seen = set()
    for name in col_names:
        if name in seen:
            issues.append(ValidationIssue(
                table=table.name,
                message=f"Duplicate column name: '{name}'.",
                severity="error",
            ))
        seen.add(name)

    index_names = [i.name for i in table.indexes]
    seen_idx = set()
    for name in index_names:
        if name in seen_idx:
            issues.append(ValidationIssue(
                table=table.name,
                message=f"Duplicate index name: '{name}'.",
                severity="warning",
            ))
        seen_idx.add(name)

    for index in table.indexes:
        for col in index.columns:
            if col not in col_names:
                issues.append(ValidationIssue(
                    table=table.name,
                    message=f"Index '{index.name}' references unknown column '{col}'.",
                    severity="error",
                ))

    return issues


def validate_schema(schema: Schema) -> ValidationResult:
    """Validate a schema and return a ValidationResult with any issues found."""
    result = ValidationResult()
    for table in schema.tables.values():
        result.issues.extend(_validate_table(table))
    return result
