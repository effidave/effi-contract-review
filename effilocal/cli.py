"""Sprint 2 CLI entry point."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from dotenv import load_dotenv

from effilocal.ai.tools import list_tools
from effilocal.config.logging import configure_logging, get_logger
from effilocal.flows import validate_doc
from effilocal.flows.analyze_doc import AnalyzeError, analyze
from effilocal.flows.chat_loop import run_chat_loop
from effilocal.flows.chat_history import (
    ConversationRecorder,
    append_history_entries,
    clear_history as clear_chat_history,
    history_entries_to_messages,
    load_history_entries,
)
from effilocal.flows.label_doc import LabelingError, label as run_label
LOGGER = get_logger("effilocal.cli")
DEFAULT_CHAT_MODEL = "gpt-4o-mini"

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

    chat_parser = subparsers.add_parser(
        "chat",
        help="Run the tool-augmented chat loop for a document.",
    )
    chat_parser.add_argument("doc_id", help="Document identifier (matches analyzed artifacts).")
    chat_parser.add_argument(
        "--question",
        required=True,
        help="Question to pose to the assistant.",
    )
    chat_parser.add_argument(
        "--trace",
        action="store_true",
        help="Force Logfire tracing to be exported for this run.",
    )
    chat_parser.add_argument(
        "--store",
        default="true",
        help="Whether to persist chat artifacts (true/false, default: true).",
    )
    chat_parser.add_argument(
        "--clear-history",
        action="store_true",
        help="Delete any stored chat history for the document before running.",
    )
    chat_modes = chat_parser.add_mutually_exclusive_group()
    chat_modes.add_argument(
        "--plan-only",
        action="store_true",
        help="Print the tool plan as JSON without executing the chat loop.",
    )
    chat_modes.add_argument(
        "--execute",
        action="store_true",
        help="Execute the chat loop (default).",
    )
    chat_parser.add_argument(
        "--model",
        default=None,
        help="Override the chat model (defaults to env EFFILOCAL_CHAT_MODEL or internal default).",
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

    if getattr(args, "command", None) == "chat":
        return _handle_chat_command(args)

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


def _handle_chat_command(args: argparse.Namespace) -> int:
    question = (args.question or "").strip()
    if not question:
        LOGGER.error("Question cannot be empty for chat command.")
        return 1

    try:
        store_artifacts = _parse_store_flag(str(args.store))
    except ValueError as exc:
        LOGGER.error(str(exc))
        return 1

    model = args.model or os.getenv("EFFILOCAL_CHAT_MODEL", DEFAULT_CHAT_MODEL)

    if args.clear_history:
        clear_chat_history(args.doc_id)

    if args.plan_only:
        plan = _build_chat_plan(
            doc_id=args.doc_id,
            question=question,
            store_artifacts=store_artifacts,
            model=model,
        )
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    if args.trace:
        os.environ.setdefault("LOGFIRE_SEND_TO_LOGFIRE", "always")

    LOGGER.info(
        "Running chat loop doc_id=%s model=%s trace=%s store=%s",
        args.doc_id,
        model,
        args.trace,
        store_artifacts,
    )

    try:
        client = _create_responses_client(trace=args.trace)
    except Exception as exc:  # pragma: no cover - runtime only
        LOGGER.error("Unable to initialise chat client: %s", exc)
        return 1

    history_messages: list[Mapping[str, Any]] | None = None
    if store_artifacts:
        existing_entries = load_history_entries(args.doc_id)
        if existing_entries:
            history_messages = history_entries_to_messages(existing_entries, args.doc_id)
    else:
        history_messages = None

    recorder = ConversationRecorder() if store_artifacts else None
    if recorder is not None:
        recorder.record_user(question, metadata={"doc_id": args.doc_id})

    try:
        answer = run_chat_loop(
            client=client,
            model=model,
            doc_id=args.doc_id,
            question=question,
            history=history_messages,
            recorder=recorder,
        )
    except Exception as exc:  # pragma: no cover - runtime only
        LOGGER.error("Chat loop execution failed: %s", exc)
        return 1

    trimmed_answer = answer.strip()
    if recorder is not None:
        recorder.record_assistant(trimmed_answer)
        append_history_entries(args.doc_id, recorder.entries)

    print(trimmed_answer)
    return 0


def _parse_store_flag(raw_value: str) -> bool:
    value = raw_value.strip().lower()
    if value in {"", "true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    raise ValueError("--store must be either true or false")


_RANGE_KEYWORDS = {"block", "blocks", "range", "paragraph", "line"}


def _build_chat_plan(*, doc_id: str, question: str, store_artifacts: bool, model: str) -> dict[str, Any]:
    follow_up_tool = _select_follow_up_tool(question)
    steps = [
        {
            "step": 1,
            "tool": "get_doc_outline",
            "arguments": {"doc_id": doc_id},
            "reason": "Map the clause hierarchy before requesting specific content.",
        },
        {
            "step": 2,
            "tool": follow_up_tool,
            "arguments": _build_follow_up_arguments(follow_up_tool, doc_id),
            "reason": f"Retrieve content relevant to the question: {question}",
        },
        {
            "step": 3,
            "tool": follow_up_tool,
            "arguments": _build_pagination_arguments(follow_up_tool, doc_id),
            "reason": "Follow the next_page token when results are truncated.",
        },
    ]

    return {
        "doc_id": doc_id,
        "question": question,
        "model": model,
        "store_artifacts": store_artifacts,
        "available_tools": [tool["function"]["name"] for tool in list_tools()],
        "steps": steps,
    }


def _select_follow_up_tool(question: str) -> str:
    q_lower = question.lower()
    if any(keyword in q_lower for keyword in _RANGE_KEYWORDS):
        return "get_content_by_range"
    return "get_section"


def _build_follow_up_arguments(tool_name: str, doc_id: str) -> dict[str, Any]:
    if tool_name == "get_section":
        return {"doc_id": doc_id, "section_id": "<determine via outline>"}
    if tool_name == "get_content_by_range":
        return {
            "doc_id": doc_id,
            "start_block": "<determine start_block after outline>",
            "end_block": "<determine end_block after outline>",
        }
    return {"doc_id": doc_id}


def _build_pagination_arguments(tool_name: str, doc_id: str) -> dict[str, Any]:
    if tool_name in {"get_section", "get_content_by_range"}:
        return {"doc_id": doc_id, "page_token": "<use next_page from previous result>"}
    return {"doc_id": doc_id}


def _create_responses_client(*, trace: bool) -> Any:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set to execute chat.")

    try:
        from openai import OpenAI  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("openai package is required to execute the chat loop") from exc

    client = OpenAI(api_key=api_key)

    if trace:
        try:
            import logfire

            logfire.instrument_openai(client)
        except Exception as exc:  # pragma: no cover - instrumentation best effort
            LOGGER.warning("Failed to instrument OpenAI client for tracing: %s", exc)

    return client


if __name__ == "__main__":
    raise SystemExit(main())
