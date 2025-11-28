
"""Paragraph block builders for direct_docx."""

from __future__ import annotations

import re
from typing import Any, Callable
from uuid import uuid4

from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

from effilocal.doc.blocks import ParagraphBlock


_HEADING_RE = re.compile(r"heading\s*(\d)", re.IGNORECASE)


def extract_indent(paragraph: Paragraph) -> dict[str, int]:
    """Return a dictionary describing paragraph indent settings."""

    fmt = paragraph.paragraph_format

    def _to_int(value: Any) -> int:
        try:
            return int(value) if value is not None else 0
        except TypeError:
            return 0

    return {
        "left": _to_int(getattr(fmt, "left_indent", None)),
        "hanging": _to_int(getattr(fmt, "hanging_indent", None)),
        "first_line": _to_int(getattr(fmt, "first_line_indent", None)),
    }


def classify_paragraph(style_name: str) -> tuple[str, int | None]:
    """Return the logical type (heading/paragraph) derived from the style name."""

    match = _HEADING_RE.search(style_name or "")
    if match:
        level = int(match.group(1))
        if 1 <= level <= 6:
            return "heading", level
    return "paragraph", None


def build_paragraph_block(
    paragraph: Paragraph,
    current_section_id: str,
    *,
    hash_provider: Callable[[str], str],
    as_dataclass: bool = False,
) -> tuple[dict[str, Any] | ParagraphBlock | None, str]:
    """Create the baseline block for ``paragraph`` and return the next section id."""

    text = paragraph.text.strip()
    if not text:
        return None, current_section_id

    style_name = paragraph.style.name if paragraph.style is not None else ""
    block_type, level = classify_paragraph(style_name)

    new_section_id = current_section_id
    if block_type == "heading":
        new_section_id = str(uuid4())

    indent = extract_indent(paragraph)
    heading_meta = {"text": text, "source": "explicit"} if block_type == "heading" else None

    para_id = paragraph._p.get(qn("w14:paraId")) or ""
    style_id = _style_id(paragraph)
    num_pr = _num_pr(paragraph)

    if as_dataclass:
        block_obj = ParagraphBlock(
            id=str(uuid4()),
            type=block_type,
            content_hash=hash_provider(text),
            text=text,
            style=style_name or "",
            level=level if block_type == "heading" else None,
            section_id=new_section_id,
            indent=indent,
            heading=heading_meta,
            para_id=para_id,
            style_id=style_id,
            num_pr=num_pr,
        )
        return block_obj, new_section_id

    block: dict[str, Any] = {
        "id": str(uuid4()),
        "type": block_type,
        "content_hash": hash_provider(text),
        "text": text,
        "style": style_name or "",
        "style_id": style_id,
        "para_id": para_id,
        "num_pr": num_pr,
        "level": level if block_type == "heading" else None,
        "section_id": new_section_id,
        "list": None,
        "table": None,
        "anchor": None,
        "metadata": None,
        "restart_group_id": None,
        "heading": heading_meta,
        "indent": indent,
    }
    return block, new_section_id


def _style_id(paragraph: Paragraph) -> str:
    try:
        style = paragraph.style
        return getattr(style, "style_id", "") or ""
    except (AttributeError, KeyError):
        return ""


def _num_pr(paragraph: Paragraph) -> dict[str, int | bool] | None:
    num_pr_nodes = paragraph._p.xpath("./*[local-name()='pPr']/*[local-name()='numPr']")
    if not num_pr_nodes:
        return None
    num_pr = num_pr_nodes[0]
    num_id_nodes = num_pr.xpath("./*[local-name()='numId']")
    if not num_id_nodes:
        return None
    num_id_val = num_id_nodes[0].get(qn("w:val"))
    try:
        num_id = int(num_id_val) if num_id_val is not None else None
    except (TypeError, ValueError):
        num_id = None
    if num_id is None:
        return None

    ilvl_nodes = num_pr.xpath("./*[local-name()='ilvl']")
    ilvl_val = ilvl_nodes[0].get(qn("w:val")) if ilvl_nodes else None
    try:
        ilvl = int(ilvl_val) if ilvl_val is not None else 0
    except (TypeError, ValueError):
        ilvl = 0

    restart_nodes = num_pr.xpath("./*[local-name()='numRestart']")
    has_restart = bool(restart_nodes)
    return {"numId": num_id, "ilvl": ilvl, "numRestart": has_restart}
