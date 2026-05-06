"""Generate structured diff reports from SchemaDiff objects."""

from dataclasses import dataclass, field
from typing import List, Optional
from sqldiff.differ import SchemaDiff
from sqldiff.formatter import format_text, format_json


@dataclass
class ReportOptions:
    output_format: str = "text"  # "text" or "json"
    include_unchanged: bool = False
    title: Optional[str] = None
    color: bool = False


@dataclass
class Report:
    diff: SchemaDiff
    options: ReportOptions = field(default_factory=ReportOptions)

    def render(self) -> str:
        """Render the report according to configured options."""
        if self.options.output_format == "json":
            return self._render_json()
        return self._render_text()

    def _render_text(self) -> str:
        lines = []
        if self.options.title:
            lines.append(f"# {self.options.title}")
            lines.append("")
        lines.append(format_text(self.diff))
        if self.options.include_unchanged:
            unchanged = _list_unchanged(self.diff)
            if unchanged:
                lines.append("\nUnchanged tables: " + ", ".join(unchanged))
        return "\n".join(lines)

    def _render_json(self) -> str:
        import json
        data = json.loads(format_json(self.diff))
        if self.options.title:
            data["title"] = self.options.title
        if self.options.include_unchanged:
            data["unchanged_tables"] = _list_unchanged(self.diff)
        return json.dumps(data, indent=2)


def _list_unchanged(diff: SchemaDiff) -> List[str]:
    """Return names of tables present in both snapshots with no changes."""
    all_old = set(diff.added_tables) | set(diff.removed_tables)
    all_modified = set(diff.modified_tables.keys())
    changed = all_old | all_modified
    # Tables that appear in modified_tables keys are changed;
    # we derive unchanged from the summary context
    unchanged = []
    for name in sorted(diff.modified_tables):
        td = diff.modified_tables[name]
        if not td.added_columns and not td.removed_columns and not td.modified_columns:
            unchanged.append(name)
    return unchanged


def build_report(diff: SchemaDiff, **kwargs) -> Report:
    """Convenience factory to create a Report with options from kwargs."""
    options = ReportOptions(**{k: v for k, v in kwargs.items() if hasattr(ReportOptions, k) or k in ReportOptions.__dataclass_fields__})
    return Report(diff=diff, options=options)
