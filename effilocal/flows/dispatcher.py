"""Validated tool dispatcher entry point for chat loop."""

from __future__ import annotations

import json
import inspect
from typing import Any, Callable, Mapping

from effilocal.tools import dispatcher as tool_dispatcher
from shared.structured import (
    ToolArgsError,
    parse_tool_args,
    parse_tool_result,
)

__all__ = ["run_tool_call"]

_TOOL_FUNCTIONS: dict[str, Callable[..., Mapping[str, Any]]] = {
    "get_doc_outline": tool_dispatcher.get_doc_outline,
    "get_section": tool_dispatcher.get_section,
    "get_content_by_range": tool_dispatcher.get_content_by_range,
    "get_related_units": tool_dispatcher.get_related_units,
    "get_by_tag": tool_dispatcher.get_by_tag,
    "get_by_clause_number": tool_dispatcher.get_by_clause_number,
}


def _prepare_arguments(tool_name: str, raw_arguments: Mapping[str, Any]) -> dict[str, Any]:
    args_model = parse_tool_args(tool_name, raw_arguments)
    kwargs = args_model.model_dump(exclude_none=True)

    func = _TOOL_FUNCTIONS[tool_name]
    sig = inspect.signature(func)
    filtered_kwargs = {key: value for key, value in kwargs.items() if key in sig.parameters}

    doc_id = filtered_kwargs.get("doc_id")
    if doc_id and not tool_dispatcher.DOC_ID_PATTERN.fullmatch(doc_id):
        raise ToolArgsError("Invalid doc_id")

    return filtered_kwargs


def _normalize_result(tool_name: str, raw_result: Mapping[str, Any]) -> Mapping[str, Any]:
    result_dict = dict(raw_result)
    result_dict.setdefault("truncated", False)
    result_dict.setdefault("next_page", None)
    result_model = parse_tool_result(result_dict)
    return result_model.model_dump()


def run_tool_call(tool_call: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Validate and execute a tool call.

    Args:
        tool_call: Mapping with a `function` entry containing the name and arguments.

    Returns:
        Normalised tool result mapping.
    """

    function_payload = tool_call.get("function")
    if not isinstance(function_payload, Mapping):
        raise ToolArgsError("Tool call missing function payload")

    name = function_payload.get("name")
    if not isinstance(name, str):
        raise ToolArgsError("Tool call missing function name")

    if name not in _TOOL_FUNCTIONS:
        raise ToolArgsError(f"Unknown tool: {name}")

    arguments = function_payload.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments or "{}")
        except json.JSONDecodeError as exc:
            raise ToolArgsError(f"Invalid arguments JSON: {exc}") from exc

    if not isinstance(arguments, Mapping):
        raise ToolArgsError("Tool arguments must be a mapping or JSON object")

    prepared_args = _prepare_arguments(name, arguments)
    tool_func = _TOOL_FUNCTIONS[name]

    try:
        raw_result = tool_func(**prepared_args)
    except FileNotFoundError as exc:
        raise ToolArgsError(str(exc)) from exc
    except ValueError as exc:
        raise ToolArgsError(str(exc)) from exc

    return _normalize_result(name, raw_result)
