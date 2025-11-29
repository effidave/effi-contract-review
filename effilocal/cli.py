"""Sprint 2 CLI entry point."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from dotenv import load_dotenv

from effilocal.config.logging import configure_logging, get_logger
from effilocal.flows import validate_doc
from effilocal.flows.analyze_doc import AnalyzeError, analyze
from effilocal.flows.label_doc import LabelingError, label as run_label
LOGGER = get_logger("effilocal.cli")

load_dotenv()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("effi-local")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display the current version of the tool.",
    )

    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Parse a .docx file into JSON artifacts.",
    )
    analyze_parser.add_argument("docx", type=Path, help="Path to the source .docx file.")
    analyze_parser.add_argument("--doc-id", required=True, help="Document UUID.")
    analyze_parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    analyze_parser.add_argument(
        "--no-emit-block-ranges",
        action="store_true",
        help="Skip emitting tag_ranges.jsonl.",
    )
    analyze_parser.add_argument(
        "--emit-ltu-tree",
        action="store_true",
        help="Emit ltu_tree.json summarising the clause hierarchy.",
    )

    label_parser = subparsers.add_parser(
        "label",
        help="Generate labels for an analyzed document (stubbed).",
    )
    label_parser.add_argument("doc_id", help="Document identifier (matches analyzed artifacts).")
    label_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Root directory containing analyzed document artifacts (default: data/)",
    )
    label_parser.add_argument(
        "--debug",
        action="store_true",
        help="Write payload.debug.json containing prompt inputs.",
    )
    label_parser.add_argument(
        "--redact",
        action="store_true",
        help="Apply snippet redaction to mask emails and phone numbers before sending to the LLM.",
    )
    label_parser.add_argument(
        "--temperature",
        type=float,
        help="Sampling temperature for labeling (default: 0.2).",
    )
    label_parser.add_argument(
        "--payload-max-chars",
        type=int,
        help="Maximum allowed characters for the labeling payload; defaults to no limit.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate previously generated JSON artifacts.",
    )
    validate_parser.add_argument("data_dir", type=Path, help="Directory containing JSON artifacts.")
    validate_parser.add_argument(
        "--deep",
        action="store_true",
        help="Run deep cross-file validation in addition to schema checks.",
    )
    validate_parser.add_argument(
        "--report",
        type=Path,
        help="Optional path for writing the validation report JSON.",
    )

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(None if argv is None else list(argv))

    if getattr(args, "version", False):
        print("effi-local sprint4 pre-chat build")
        return 0

    if getattr(args, "command", None) == "analyze":
        LOGGER.info(
            "Analyzing docx path=%s doc_id=%s out=%s",
            args.docx,
            args.doc_id,
            args.out,
        )
        try:
            analyze(
                args.docx,
                doc_id=args.doc_id,
                out_dir=args.out,
                emit_block_ranges=not args.no_emit_block_ranges,
                emit_ltu_tree=args.emit_ltu_tree,
            )
        except AnalyzeError as exc:
            LOGGER.error("Document analysis failed: %s", exc)
            return 1

        if args.emit_ltu_tree:
            LOGGER.info("Requested LTU tree emission (ltu_tree.json).")
        if args.no_emit_block_ranges:
            LOGGER.info("Skipping tag_ranges.jsonl emission as requested.")
        return 0

    if getattr(args, "command", None) == "label":
        LOGGER.info(
            "Labeling document doc_id=%s data_dir=%s debug=%s temperature=%s redact=%s payload_max_chars=%s",
            args.doc_id,
            args.data_dir,
            args.debug,
            args.temperature if args.temperature is not None else "default",
            args.redact,
            args.payload_max_chars if args.payload_max_chars is not None else "none",
        )
        try:
            run_label(
                args.doc_id,
                data_dir=args.data_dir,
                debug=args.debug,
                temperature=args.temperature,
                redact=args.redact,
                payload_max_chars=args.payload_max_chars,
            )
        except LabelingError as exc:
            LOGGER.error("Document labeling failed: %s", exc)
            return 1
        return 0

    if getattr(args, "command", None) == "validate":
        report = validate_doc.validate_directory(args.data_dir, deep=args.deep)
        output = {
            "ok": report.ok,
            "errors": [asdict(issue) for issue in report.errors],
        }
        payload = json.dumps(output, indent=2)
        if args.report:
            args.report.write_text(payload + "\n", encoding="utf-8")
            LOGGER.info("Validation report written to %s", args.report)
        else:
            print(payload)
        return 0 if report.ok else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
