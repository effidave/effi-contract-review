"""Tool probing harness using the OpenAI Responses API."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Sequence

from effilocal.ai.dispatch import dispatch_tool
from effilocal.ai.tools import list_tools


def run_probe(
    *,
    client: Any,
    model: str,
    messages: Sequence[Mapping[str, Any]],
    temperature: float = 0.2,
    tools: Iterable[Mapping[str, Any]] | None = None,
) -> str:
    """Execute a single Responses API turn with tool handling."""
    tool_specs = list(tools) if tools is not None else list_tools()

    stream = client.responses.stream(
        model=model,
        input=list(messages),
        tools=tool_specs,
        temperature=temperature,
    )

    final_text_parts: list[str] = []
    cache: dict[tuple[str, str], str] = {}
    with stream as events:
        for event in events:
            event_type = getattr(event, "type", None)
            if event_type == "response.tool_call":
                _handle_tool_call(event, cache)
            elif event_type == "response.output_text":
                final_text_parts.append(getattr(event, "text", ""))
            elif event_type == "response.completed":
                response_obj = getattr(event, "response", None)
                if response_obj is not None:
                    if not final_text_parts:
                        final_text_parts.append(
                            getattr(response_obj, "output_text", "") or ""
                        )
                break
            elif event_type == "response.error":
                error = getattr(event, "error", "Unknown error")
                raise RuntimeError(f"Responses API error: {error}")

    return "".join(final_text_parts).strip()


def _handle_tool_call(event: Any, cache: dict[tuple[str, str], str]) -> None:
    function = getattr(event, "function", None)
    if function is None:
        raise RuntimeError("Tool call event missing function payload")

    name = getattr(function, "name", None)
    raw_args = getattr(function, "arguments", "{}")
    if not isinstance(raw_args, str):
        raise RuntimeError("Tool call arguments must be a JSON string")

    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid tool call arguments for {name}: {exc}") from exc

    if not isinstance(name, str) or not name:
        raise RuntimeError("Tool call function name must be a non-empty string")
    if not isinstance(args, Mapping):
        raise ValueError("Tool call arguments must decode to a JSON object")

    canonical_args = json.dumps(args, sort_keys=True)
    cache_key = (name, canonical_args)
    if cache_key in cache:
        cached_result = cache[cache_key]
        event.result = cached_result
        submit = getattr(event, "submit", None)
        if callable(submit):
            submit()
        return

    try:
        result = dispatch_tool(name, dict(args))
        payload = result
    except Exception as exc:
        error_message = _format_error_message(exc)
        payload = {"error": error_message}
    result_json = json.dumps(payload, ensure_ascii=False)
    cache[cache_key] = result_json
    event.result = result_json

    submit = getattr(event, "submit", None)
    if callable(submit):
        submit()


def _format_error_message(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        message = exc.__class__.__name__
    else:
        message = f"{exc.__class__.__name__}: {message}"
    return message
