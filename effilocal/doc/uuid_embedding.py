"""UUID embedding via Word content controls (SDT elements).

This module provides functions to embed and extract UUIDs from Word documents
using Structured Document Tags (SDTs / content controls). UUIDs are stored as
tag values in the format "effi:block:<uuid>".

Content controls survive save/close/reopen cycles in Word and can persist
through copy/paste operations within the same document.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Iterator
from uuid import uuid4

from docx import Document
from docx.oxml import register_element_cls
from docx.oxml.ns import nsmap, qn
from docx.oxml.xmlchemy import BaseOxmlElement
from lxml import etree

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "embed_block_uuids",
    "extract_block_uuids",
    "remove_all_uuid_controls",
    "get_paragraph_uuid",
    "set_paragraph_uuid",
    "EFFI_TAG_PREFIX",
]

# Prefix for effi block tags in content controls
EFFI_TAG_PREFIX = "effi:block:"

# Word XML namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"


def _make_sdt_element(uuid_value: str, inner_xml: etree._Element) -> etree._Element:
    """Create an SDT (content control) element wrapping the given content.

    The SDT structure is:
    <w:sdt>
        <w:sdtPr>
            <w:tag w:val="effi:block:uuid-here"/>
            <w:id w:val="123456"/>
        </w:sdtPr>
        <w:sdtContent>
            <!-- paragraph or other content -->
        </w:sdtContent>
    </w:sdt>

    Args:
        uuid_value: The UUID to embed as the tag value
        inner_xml: The XML element to wrap (typically a paragraph)

    Returns:
        The constructed SDT element
    """
    # Create SDT structure
    sdt = etree.Element(qn("w:sdt"))

    # SDT properties
    sdt_pr = etree.SubElement(sdt, qn("w:sdtPr"))

    # Tag with UUID
    tag = etree.SubElement(sdt_pr, qn("w:tag"))
    tag.set(qn("w:val"), f"{EFFI_TAG_PREFIX}{uuid_value}")

    # Unique ID (use hash of UUID for consistency)
    sdt_id = etree.SubElement(sdt_pr, qn("w:id"))
    sdt_id.set(qn("w:val"), str(abs(hash(uuid_value)) % 2147483647))

    # SDT content wrapper
    sdt_content = etree.SubElement(sdt, qn("w:sdtContent"))

    # Move the inner content into the SDT
    sdt_content.append(inner_xml)

    return sdt


def _extract_tag_value(sdt_element: etree._Element) -> str | None:
    """Extract the tag value from an SDT element.

    Args:
        sdt_element: An SDT element

    Returns:
        The tag value if it's an effi block tag, else None
    """
    sdt_pr = sdt_element.find(qn("w:sdtPr"))
    if sdt_pr is None:
        return None

    tag = sdt_pr.find(qn("w:tag"))
    if tag is None:
        return None

    val = tag.get(qn("w:val"), "")
    if val.startswith(EFFI_TAG_PREFIX):
        return val[len(EFFI_TAG_PREFIX) :]

    return None


def _iter_sdt_elements(document: Document) -> Iterator[etree._Element]:
    """Iterate over all SDT elements in the document body."""
    body = document.element.body
    for sdt in body.iter(qn("w:sdt")):
        yield sdt


def _iter_paragraphs_with_index(document: Document) -> Iterator[tuple[int, etree._Element]]:
    """Iterate over paragraph elements with their index in document order."""
    body = document.element.body
    idx = 0
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield idx, child
            idx += 1
        elif child.tag == qn("w:sdt"):
            # Check if SDT contains a paragraph
            sdt_content = child.find(qn("w:sdtContent"))
            if sdt_content is not None:
                for p in sdt_content.findall(qn("w:p")):
                    yield idx, p
                    idx += 1


def get_paragraph_uuid(paragraph_element: etree._Element) -> str | None:
    """Get the UUID from a paragraph's parent SDT if present.

    Args:
        paragraph_element: A w:p element

    Returns:
        The UUID string if the paragraph is wrapped in an effi SDT, else None
    """
    parent = paragraph_element.getparent()
    if parent is None:
        return None

    # Check if parent is sdtContent
    if parent.tag == qn("w:sdtContent"):
        sdt = parent.getparent()
        if sdt is not None and sdt.tag == qn("w:sdt"):
            return _extract_tag_value(sdt)

    return None


def set_paragraph_uuid(
    document: Document,
    paragraph_element: etree._Element,
    uuid_value: str,
) -> bool:
    """Wrap a paragraph in an SDT with the given UUID.

    If the paragraph is already wrapped in an effi SDT, updates the tag value.

    Args:
        document: The Document object (for context)
        paragraph_element: The w:p element to wrap
        uuid_value: The UUID to embed

    Returns:
        True if successful, False if the paragraph couldn't be wrapped
    """
    parent = paragraph_element.getparent()
    if parent is None:
        return False

    # Check if already wrapped in an effi SDT
    if parent.tag == qn("w:sdtContent"):
        sdt = parent.getparent()
        if sdt is not None and sdt.tag == qn("w:sdt"):
            existing_uuid = _extract_tag_value(sdt)
            if existing_uuid is not None:
                # Update existing tag
                sdt_pr = sdt.find(qn("w:sdtPr"))
                if sdt_pr is not None:
                    tag = sdt_pr.find(qn("w:tag"))
                    if tag is not None:
                        tag.set(qn("w:val"), f"{EFFI_TAG_PREFIX}{uuid_value}")
                        return True
        return False

    # Create new SDT wrapper
    index = list(parent).index(paragraph_element)

    # Remove paragraph from parent
    parent.remove(paragraph_element)

    # Create SDT wrapping the paragraph
    sdt = _make_sdt_element(uuid_value, paragraph_element)

    # Insert SDT at original position
    parent.insert(index, sdt)

    return True


def embed_block_uuids(
    doc_or_path: Document | str | "Path",
    blocks: list[dict],
    *,
    overwrite: bool = False,
) -> dict[str, str]:
    """Embed UUIDs from blocks into the document as content controls.

    Each block's "id" field is used as the UUID. Blocks are matched to
    paragraphs by their "para_idx" field (0-based index).

    Args:
        doc_or_path: Document object or path to .docx file
        blocks: List of block dicts with "id" and "para_idx" fields
        overwrite: If True, overwrite existing UUIDs; if False, skip already-wrapped paragraphs

    Returns:
        Mapping of block_id to paragraph index for successfully embedded blocks
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
        save_path = Path(doc_or_path)
    else:
        document = doc_or_path
        save_path = None

    # Build index of para_idx -> paragraph element
    para_elements: dict[int, etree._Element] = {}
    for idx, elem in _iter_paragraphs_with_index(document):
        para_elements[idx] = elem

    embedded: dict[str, str] = {}

    for block in blocks:
        block_id = block.get("id")
        para_idx = block.get("para_idx")

        if block_id is None or para_idx is None:
            continue

        para_elem = para_elements.get(para_idx)
        if para_elem is None:
            continue

        # Check if already has UUID
        existing = get_paragraph_uuid(para_elem)
        if existing is not None and not overwrite:
            embedded[block_id] = str(para_idx)
            continue

        # Embed UUID
        if set_paragraph_uuid(document, para_elem, block_id):
            embedded[block_id] = str(para_idx)

    # Save if we loaded from path
    if save_path is not None:
        document.save(str(save_path))

    return embedded


def extract_block_uuids(doc_or_path: Document | str | "Path") -> dict[str, int]:
    """Extract UUID → paragraph index mapping from embedded content controls.

    Args:
        doc_or_path: Document object or path to .docx file

    Returns:
        Mapping of UUID string to paragraph index (0-based)
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
    else:
        document = doc_or_path

    uuid_to_idx: dict[str, int] = {}

    for idx, para_elem in _iter_paragraphs_with_index(document):
        uuid_val = get_paragraph_uuid(para_elem)
        if uuid_val is not None:
            uuid_to_idx[uuid_val] = idx

    return uuid_to_idx


def remove_all_uuid_controls(doc_or_path: Document | str | "Path") -> int:
    """Remove all effi content controls from the document.

    The content inside the controls is preserved; only the SDT wrapper is removed.

    Args:
        doc_or_path: Document object or path to .docx file

    Returns:
        Number of controls removed
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
        save_path = Path(doc_or_path)
    else:
        document = doc_or_path
        save_path = None

    removed = 0
    body = document.element.body

    # Find all effi SDTs
    effi_sdts = []
    for sdt in list(body.iter(qn("w:sdt"))):
        if _extract_tag_value(sdt) is not None:
            effi_sdts.append(sdt)

    for sdt in effi_sdts:
        parent = sdt.getparent()
        if parent is None:
            continue

        # Get the content inside the SDT
        sdt_content = sdt.find(qn("w:sdtContent"))
        if sdt_content is None:
            continue

        # Find position of SDT in parent
        index = list(parent).index(sdt)

        # Move all children of sdtContent to parent
        for child in list(sdt_content):
            parent.insert(index, child)
            index += 1

        # Remove the now-empty SDT
        parent.remove(sdt)
        removed += 1

    if save_path is not None:
        document.save(str(save_path))

    return removed
