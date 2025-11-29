from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from effilocal.doc.numbering_inspector import NumberingInspector

DEFAULT_COLUMNS = [
    "idx",
    "paraId",
    "styleId",
    "numId",
    "abstractNumId",
    "ilvl",
    "rendered_number",
    "pattern",
    "format",
    "counters",
    "num_restart",
    "source",
]


def parse_args() -> argparse.Namespace:
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Inspect numbering metadata for a .docx using the shared NumberingInspector.",
    )
    parser.add_argument("docx", type=Path, help="Path to the .docx to inspect.")
    parser.add_argument(
        "--idx-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Only include paragraphs whose idx is within the inclusive range.",
    )
    parser.add_argument(
        "--para-ids",
        nargs="+",
        metavar="PARA_ID",
        help="Only include paragraphs whose paraId matches one of the provided values.",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        metavar="COLUMN",
        help="Columns to display (defaults to a concise subset).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the main rows to a JSON or CSV file instead of stdout.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Emit debug rows (binding source/overrides/counters).",
    )
    parser.add_argument(
        "--debug-output",
        type=Path,
        help="Write debug rows to a JSON or CSV file. Implies --debug.",
    )
    parser.add_argument(
        "--logfire",
        action="store_true",
        help="Enable Logfire instrumentation for inspector events (requires logfire installed/token).",
    )
    parser.add_argument(
        "--include-text",
        action="store_true",
        help="Include the paragraph text column in the stdout table.",
    )
    return parser.parse_args()


def stringify(value: Any) -> str:
    """Return a human-friendly string for tabular/CSV output."""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def filter_rows(
    rows: Iterable[dict[str, Any]],
    idx_range: tuple[int, int] | None,
    para_ids: set[str] | None,
) -> list[dict[str, Any]]:
    """Filter rows by idx range and paraId set."""
    filtered: list[dict[str, Any]] = []
    for row in rows:
        idx = row.get("idx")
        para_id = row.get("paraId")
        if idx_range is not None:
            start, end = idx_range
            if not isinstance(idx, int) or idx < start or idx > end:
                continue
        if para_ids is not None and para_id not in para_ids:
            continue
        filtered.append(row)
    return filtered


def print_table(rows: Sequence[dict[str, Any]], columns: Sequence[str]) -> None:
    """Print a simple table to stdout."""
    if not rows:
        print("No numbered paragraphs matched the filter.")
        return

    col_widths = {
        col: max(len(col), *(len(stringify(row.get(col, ""))) for row in rows)) for col in columns
    }

    def render_row(row: dict[str, Any]) -> str:
        cells = [stringify(row.get(col, "")).ljust(col_widths[col]) for col in columns]
        return " | ".join(cells)

    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    divider = "-+-".join("-" * col_widths[col] for col in columns)
    print(header)
    print(divider)
    for row in rows:
        print(render_row(row))


def write_records(path: Path, rows: Sequence[dict[str, Any]], columns: Sequence[str]) -> None:
    """Write rows to JSON or CSV based on the file suffix."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(json.dumps(list(rows), ensure_ascii=False, indent=2), encoding="utf-8")
        return

    fieldnames = list(columns)
    with path.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: stringify(row.get(field, "")) for field in fieldnames})


def main() -> None:
    args = parse_args()
    columns = args.columns or DEFAULT_COLUMNS
    if args.include_text and "text" not in columns:
        columns = list(columns) + ["text"]

    idx_range = tuple(args.idx_range) if args.idx_range else None
    para_ids = set(args.para_ids) if args.para_ids else None

    inspector = NumberingInspector.from_docx(args.docx)
    rows, debug_rows = inspector.analyze(
        debug=args.debug or bool(args.debug_output),
        logging_enabled=args.logfire,
    )

    rows = filter_rows(rows, idx_range, para_ids)
    debug_rows = (
        filter_rows(debug_rows, idx_range, para_ids) if args.debug or args.debug_output else []
    )

    if args.output:
        write_records(args.output, rows, columns)
    else:
        print_table(rows, columns)

    if args.debug_output:
        debug_columns = list(debug_rows[0].keys()) if debug_rows else list(columns)
        write_records(args.debug_output, debug_rows, debug_columns)
    elif args.debug:
        print("\nDebug rows:")
        debug_columns = list(debug_rows[0].keys()) if debug_rows else list(columns)
        print_table(debug_rows, debug_columns)


if __name__ == "__main__":
    main()
