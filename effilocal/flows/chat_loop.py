"""Skeleton chat loop using the OpenAI Responses API."""

from __future__ import annotations

import json
from copy import deepcopy
import logging
from pprint import pformat
from pathlib import Path
from typing import Any, Mapping, Sequence

from effilocal.ai.tools import list_tools
from effilocal.prompts.chat import get_chat_system_prompt
from effilocal.logging import get_tracer
import logfire
from shared.structured import ToolArgsError, parse_tool_result
from effilocal.flows.chat_history import ConversationRecorder, format_user_prompt

__all__ = ["run_chat_loop"]

_DEVELOPER_PROMPT_PATH = Path("prompts/chat_tool_use.md")
_MAX_PAGINATION_STEPS = 20
LOGGER = logging.getLogger(__name__)


def _load_developer_prompt() -> str:
    if not _DEVELOPER_PROMPT_PATH.is_file():
        raise FileNotFoundError(
            f"Developer prompt not found: {_DEVELOPER_PROMPT_PATH}"
        )
    return _DEVELOPER_PROMPT_PATH.read_text(encoding="utf-8")


def run_chat_loop(
    *,
    client: Any,
    model: str,
    doc_id: str,
    question: str,
    history: Sequence[Mapping[str, Any]] | None = None,
    recorder: ConversationRecorder | None = None,
) -> str:
    """
    Execute a skeleton chat loop against the Responses API.

    The implementation intentionally stops after the first completed response;
    later sprints will extend this with tool handling and streaming updates.
    """

    system_prompt = get_chat_system_prompt()
    developer_prompt = _load_developer_prompt()

    messages: list[Mapping[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "developer", "content": developer_prompt},
    ]
    if history:
        messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": format_user_prompt(doc_id, question),
        }
    )

    with get_tracer(
        "chat",
        doc_id=doc_id,
        question=question,
        model=model,
    ):
        with logfire.span(
            "chat.tool_selection",
            _span_name="chat.tool_selection",
        ) as selection_span:
            tools = list_tools()
            if selection_span is not None:
                selection_span.set_attribute("tool_count", len(tools))

        with logfire.span(
            "chat.budget",
            _span_name="chat.budget",
            message_count=len(messages),
        ):
            # Budgeting helper will plug in here once token estimates are wired up.
            pass

        stream = client.responses.stream(
            model=model,
            input=messages,
            tools=tools,
            parallel_tool_calls=False,
        )

        final_text_parts: list[str] = []
        with stream as events:
            for event in events:
                event_type = getattr(event, "type", None)
                if LOGGER.isEnabledFor(logging.DEBUG):
                    LOGGER.debug(
                        "stream event=%s payload=%s",
                        event_type,
                        pformat(getattr(event, "__dict__", event)),
                    )
                if event_type == "response.output_text":
                    if LOGGER.isEnabledFor(logging.DEBUG):
                        LOGGER.debug("assistant chunk: %s", getattr(event, "text", ""))
                    final_text_parts.append(getattr(event, "text", ""))
                elif event_type == "response.tool_call":
                    if LOGGER.isEnabledFor(logging.DEBUG):
                        func = getattr(event, "function", None)
                        LOGGER.debug("tool call event: %s", getattr(func, "name", None))
                    _handle_tool_call(event, recorder=recorder)
                elif event_type == "response.completed":
                    response_obj = getattr(event, "response", None)
                    if response_obj is not None:
                        final_text_parts.append(
                            getattr(response_obj, "output_text", "") or ""
                        )
                    break
                elif event_type == "response.error":
                    error = getattr(event, "error", "Unknown error")
                    raise RuntimeError(f"Responses API error: {error}")

        with logfire.span(
            "chat.compose",
            _span_name="chat.compose",
            part_count=len(final_text_parts),
        ):
            composed = "".join(final_text_parts).strip()
            if not composed:
                composed = "[no assistant output]"

        with logfire.span(
            "chat.finalize",
            _span_name="chat.finalize",
            response_length=len(composed),
        ):
            return composed


def _handle_tool_call(event: Any, *, recorder: ConversationRecorder | None) -> None:
    function = getattr(event, "function", None)
    if function is None:
        raise RuntimeError("Tool call event missing function payload")

    name = getattr(function, "name", None)
    if not isinstance(name, str) or not name:
        raise RuntimeError("Tool call missing function name")

    raw_arguments = getattr(function, "arguments", "{}")
    if not isinstance(raw_arguments, str):
        raise RuntimeError("Tool call arguments must be provided as a JSON string")

    try:
        arguments: dict[str, Any] = json.loads(raw_arguments or "{}")
    except json.JSONDecodeError as exc:
        with logfire.span(
            "chat.args_validation",
            _span_name="chat.args_validation",
            tool=name,
            invalid_json=True,
        ):
            raise ValueError(f"Invalid tool call arguments for {name}: {exc}") from exc

    with logfire.span(
        "chat.args_validation",
        _span_name="chat.args_validation",
        tool=name,
        argument_keys=sorted(arguments.keys()),
    ):
        validated_arguments = dict(arguments)

    try:
        merged_result = _execute_tool_with_pagination(name, validated_arguments)
        payload = merged_result
    except ToolArgsError as exc:
        payload = {"error": str(exc) or exc.__class__.__name__}

    if recorder is not None:
        recorder.record_tool_call(name, validated_arguments, payload)

    event.result = json.dumps(payload, ensure_ascii=False)
    submit = getattr(event, "submit", None)
    if callable(submit):
        submit()


def _execute_tool_with_pagination(
    tool_name: str,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    from effilocal.flows.dispatcher import run_tool_call
    base_arguments = dict(arguments)
    pages = []
    visited_tokens: set[str | int] = set()
    current_arguments = dict(base_arguments)

    with logfire.span(
        "chat.dispatch",
        _span_name="chat.dispatch",
        tool=tool_name,
        base_argument_keys=sorted(base_arguments.keys()),
    ):
        for page_index in range(_MAX_PAGINATION_STEPS):
            payload = {
                "function": {
                    "name": tool_name,
                    "arguments": current_arguments,
                }
            }
            raw_result = run_tool_call(payload)
            result_model = parse_tool_result(raw_result)

            with logfire.span(
                "chat.pagination",
                _span_name="chat.pagination",
                tool=tool_name,
                page=page_index,
                truncated=result_model.truncated,
                next_page_token=result_model.next_page,
            ):
                pages.append(result_model)

            if not result_model.truncated:
                break

            next_page = result_model.next_page
            if next_page is None:
                raise ToolArgsError("Tool result truncated without a next_page token")
            if next_page in visited_tokens:
                raise ToolArgsError("Detected repeated pagination token")

            visited_tokens.add(next_page)
            current_arguments = dict(base_arguments)
            current_arguments["page_token"] = next_page
        else:
            raise ToolArgsError("Exceeded maximum pagination depth")

    merged = _merge_paginated_results(pages)

    with logfire.span(
        "chat.redaction",
        _span_name="chat.redaction",
        tool=tool_name,
        redaction_applied=_detect_redaction(merged),
    ):
        return merged


def _merge_paginated_results(pages: Sequence[Any]) -> dict[str, Any]:
    if not pages:
        return {"truncated": False, "next_page": None}

    merged: dict[str, Any] = {"truncated": False, "next_page": None}

    for page in pages:
        extras = getattr(page, "model_extra", {})
        for key, value in extras.items():
            if isinstance(value, list):
                merged.setdefault(key, [])
                merged[key].extend(_clone_list(value))
            elif key not in merged:
                merged[key] = _clone_value(value)

    return merged


def _clone_list(items: Sequence[Any]) -> list[Any]:
    cloned: list[Any] = []
    for item in items:
        if isinstance(item, Mapping):
            cloned.append({k: deepcopy(v) for k, v in item.items()})
        else:
            cloned.append(deepcopy(item))
    return cloned


def _clone_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: deepcopy(v) for k, v in value.items()}
    if isinstance(value, list):
        return _clone_list(value)
    return deepcopy(value)


def _detect_redaction(result: Mapping[str, Any]) -> bool:
    if result.get("redacted"):
        return True

    blocks = result.get("blocks")
    if isinstance(blocks, Sequence):
        for block in blocks:
            if isinstance(block, Mapping):
                text = str(block.get("text", "") or "")
                if "█" in text or "[REDACTED]" in text.upper():
                    return True
    return False
