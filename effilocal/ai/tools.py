"""Responses API tool declarations for Sprint 3."""

from __future__ import annotations

from typing import Dict, List, Tuple, Type

from openai import pydantic_function_tool

from pydantic import BaseModel
from shared.structured import (
    ContentRangeArgs,
    DocOutlineArgs,
    GetByClauseNumberArgs,
    GetByTagArgs,
    GetSectionArgs,
    RelatedUnitsArgs,
)

ToolModel = Type[BaseModel]

_TOOL_DEFS: List[Tuple[ToolModel, str, str]] = [
    (
        DocOutlineArgs,
        "get_doc_outline",
        "Return the document outline with section ids, titles, levels, and counts.",
    ),
    (
        ContentRangeArgs,
        "get_content_by_range",
        "Retrieve blocks of text for the specified block index range.",
    ),
    (
        GetSectionArgs,
        "get_section",
        "Fetch the blocks belonging to a section identified by section_id.",
    ),
    (
        RelatedUnitsArgs,
        "get_related_units",
        "Return related block ids (parent, siblings, children) for the supplied block.",
    ),
    (
        GetByTagArgs,
        "get_by_tag",
        "Return tag ranges and associated blocks for the specified label.",
    ),
    (
        GetByClauseNumberArgs,
        "get_by_clause_number",
        "Return block ids that match the supplied clause number string.",
    ),
]


def list_tools() -> List[Dict[str, object]]:
    """Return the tool descriptors for Responses API function calling."""

    tools: List[Dict[str, object]] = []
    for model, name, description in _TOOL_DEFS:
        tools.append(pydantic_function_tool(model, name=name, description=description))
    return tools
