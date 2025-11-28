"""Host-facing dispatcher wrapper with schema validation."""

from __future__ import annotations

from typing import Any, Mapping

from effilocal.tools import dispatcher, schemas


def dispatch_tool(tool_name: str, args: Mapping[str, Any]) -> dict[str, Any]:
    """Validate inputs, invoke the dispatcher, and validate outputs."""
    resolved_args = dict(args)
    schemas.validate_tool_input(tool_name, resolved_args)

    try:
        handler = getattr(dispatcher, tool_name)
    except AttributeError as exc:
        raise ValueError(f"Unknown tool: {tool_name}") from exc

    result = handler(**resolved_args)
    if not isinstance(result, Mapping):
        raise TypeError("Dispatcher returned a non-mapping result")

    result_dict = dict(result)
    schemas.validate_tool_output(tool_name, result_dict)
    return result_dict
