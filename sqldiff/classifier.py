"""Classify diff changes by risk level (low / medium / high)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from sqldiff.differ import SchemaDiff


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RiskItem:
    table: str
    description: str
    level: RiskLevel

    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.table}: {self.description}"


@dataclass
class ClassificationReport:
    items: List[RiskItem] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def by_level(self, level: RiskLevel) -> List[RiskItem]:
        return [i for i in self.items if i.level == level]

    def highest_risk(self) -> RiskLevel:
        if any(i.level == RiskLevel.HIGH for i in self.items):
            return RiskLevel.HIGH
        if any(i.level == RiskLevel.MEDIUM for i in self.items):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def __str__(self) -> str:
        if self.is_empty():
            return "No risk items."
        return "\n".join(str(i) for i in self.items)


def classify_diff(diff: SchemaDiff) -> ClassificationReport:
    """Analyse a SchemaDiff and assign a risk level to each change."""
    items: List[RiskItem] = []

    for table_name in diff.tables_added:
        items.append(RiskItem(table_name, "Table added", RiskLevel.LOW))

    for table_name in diff.tables_removed:
        items.append(RiskItem(table_name, "Table removed", RiskLevel.HIGH))

    for table_name, table_diff in diff.tables_modified.items():
        for col in table_diff.columns_added:
            level = RiskLevel.MEDIUM if col.not_null and col.default is None else RiskLevel.LOW
            items.append(RiskItem(table_name, f"Column added: {col.name}", level))

        for col in table_diff.columns_removed:
            items.append(RiskItem(table_name, f"Column removed: {col.name}", RiskLevel.HIGH))

        for col_diff in table_diff.columns_modified:
            if col_diff.type_changed:
                items.append(RiskItem(table_name, f"Column type changed: {col_diff.name}", RiskLevel.HIGH))
            else:
                items.append(RiskItem(table_name, f"Column altered: {col_diff.name}", RiskLevel.MEDIUM))

        for idx in table_diff.indexes_added:
            items.append(RiskItem(table_name, f"Index added: {idx.name}", RiskLevel.LOW))

        for idx in table_diff.indexes_removed:
            items.append(RiskItem(table_name, f"Index removed: {idx.name}", RiskLevel.MEDIUM))

    return ClassificationReport(items=items)
