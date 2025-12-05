
"""Paragraph block builders for direct_docx."""

from __future__ import annotations

import re
from typing import Any, Callable, Optional
from uuid import uuid4

from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

from effilocal.doc.amended_paragraph import AmendedParagraph
from effilocal.doc.blocks import ParagraphBlock


_HEADING_RE = re.compile(r"heading\s*(\d)", re.IGNORECASE)


def has_page_break_before(paragraph: Paragraph) -> bool:
    """Check if paragraph has a page break before it.
    
    Detects:
    1. Explicit page breaks (<w:br w:type="page"/>) in preceding content
    2. Word's lastRenderedPageBreak marker (soft page break from last render)
    3. Page break before paragraph property (w:pageBreakBefore)
    """
    p_elem = paragraph._p
    
    # Check for pageBreakBefore in paragraph properties
    pPr = p_elem.find(qn('w:pPr'))
    if pPr is not None:
        page_break_before = pPr.find(qn('w:pageBreakBefore'))
        if page_break_before is not None:
            # Check if it's not explicitly disabled (w:val="0" or w:val="false")
            val = page_break_before.get(qn('w:val'))
            if val not in ('0', 'false'):
                return True
    
    # Check for lastRenderedPageBreak in runs (soft page break marker from Word)
    # This indicates where Word calculated a page break when the doc was last saved
    for run in p_elem.findall(qn('w:r')):
        if run.find(qn('w:lastRenderedPageBreak')) is not None:
            return True
    
    return False


def has_explicit_page_break(paragraph: Paragraph) -> bool:
    """Check if paragraph contains an explicit hard page break (<w:br w:type="page"/>)."""
    p_elem = paragraph._p
    
    for run in p_elem.findall(qn('w:r')):
        for br in run.findall(qn('w:br')):
            if br.get(qn('w:type')) == 'page':
                return True
    
    return False


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
    amended: Optional[AmendedParagraph] = None,
) -> tuple[dict[str, Any] | ParagraphBlock | None, str]:
    """Create the baseline block for ``paragraph`` and return the next section id.
    
    Args:
        paragraph: The Word paragraph to process
        current_section_id: Current section identifier
        hash_provider: Function to generate content hashes
        as_dataclass: If True, return ParagraphBlock instead of dict
        amended: Optional AmendedParagraph wrapper for track changes support.
                 If provided, uses amended_text (visible text with insertions,
                 without deletions) instead of paragraph.text.
    """
    # Use amended_text if AmendedParagraph provided, otherwise fall back to standard text
    if amended is not None:
        text = amended.amended_text.strip()
    else:
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
    
    # Detect page breaks
    page_break_before = has_page_break_before(paragraph)
    page_break_after = has_explicit_page_break(paragraph)

    if as_dataclass:
        block_obj = ParagraphBlock(
            id=None,  # ID assigned later by assign_block_ids()
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
            page_break_before=page_break_before if page_break_before else None,
            page_break_after=page_break_after if page_break_after else None,
        )
        return block_obj, new_section_id

    block: dict[str, Any] = {
        "id": None,  # ID assigned later by assign_block_ids()
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
        "page_break_before": page_break_before if page_break_before else None,
        "page_break_after": page_break_after if page_break_after else None,
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
