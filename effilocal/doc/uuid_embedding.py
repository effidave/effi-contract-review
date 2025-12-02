"""UUID embedding via Word content controls (SDT elements).

This module provides functions to embed and extract UUIDs from Word documents
using Structured Document Tags (SDTs / content controls). UUIDs are stored as
tag values in the format "effi:block:<uuid>".

Content controls survive save/close/reopen cycles in Word and can persist
through copy/paste operations within the same document.

Supports embedding UUIDs in:
- Top-level body paragraphs (matched by para_idx)
- Paragraphs inside existing SDT content controls
- Paragraphs inside table cells (matched by table position: table_idx, row, col)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, Union
from uuid import uuid4

from docx import Document
from docx.oxml.ns import qn
from lxml import etree

if TYPE_CHECKING:
    from pathlib import Path

__all__ = [
    "embed_block_uuids",
    "extract_block_uuids",
    "extract_block_uuids_legacy",
    "remove_all_uuid_controls",
    "get_paragraph_uuid",
    "set_paragraph_uuid",
    "EFFI_TAG_PREFIX",
    "BlockKey",
    "ParaKey",
    "TableCellKey",
]

# Prefix for effi block tags in content controls
EFFI_TAG_PREFIX = "effi:block:"

# Word XML namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"


@dataclass(frozen=True)
class ParaKey:
    """Key for a top-level paragraph block."""
    para_idx: int


@dataclass(frozen=True)
class TableCellKey:
    """Key for a table cell block."""
    table_idx: int
    row: int
    col: int


# Union type for block keys
BlockKey = Union[ParaKey, TableCellKey]


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
    """Iterate over top-level paragraph elements with their index in document order.
    
    This only yields top-level body paragraphs (not those in tables).
    For table cell paragraphs, use _iter_all_blocks().
    """
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


def _iter_all_blocks(document: Document) -> Iterator[tuple[BlockKey, etree._Element]]:
    """Iterate over ALL paragraph elements in the document, including those in tables.
    
    Yields tuples of (BlockKey, paragraph_element) where BlockKey is either:
    - ParaKey(para_idx) for top-level body paragraphs
    - TableCellKey(table_idx, row, col) for paragraphs inside table cells
    
    This traverses:
    - Top-level body paragraphs (including those inside SDT content controls)
    - Tables → rows → cells → paragraphs
    - SDT content controls containing tables or paragraphs
    
    Note: Table cells may contain multiple paragraphs. Only the FIRST paragraph
    in each cell is yielded with the cell's key, as blocks.jsonl captures
    cell content as a single block.
    """
    body = document.element.body
    para_idx = 0
    table_idx = 0
    
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            # Top-level paragraph
            yield ParaKey(para_idx), child
            para_idx += 1
            
        elif child.tag == qn("w:tbl"):
            # Table - iterate rows and cells
            yield from _iter_table_cells(child, table_idx)
            table_idx += 1
            
        elif child.tag == qn("w:sdt"):
            # SDT content control - may contain paragraphs or tables
            sdt_content = child.find(qn("w:sdtContent"))
            if sdt_content is not None:
                for sdt_child in sdt_content:
                    if sdt_child.tag == qn("w:p"):
                        yield ParaKey(para_idx), sdt_child
                        para_idx += 1
                    elif sdt_child.tag == qn("w:tbl"):
                        yield from _iter_table_cells(sdt_child, table_idx)
                        table_idx += 1


def _iter_table_cells(
    table_element: etree._Element,
    table_idx: int,
) -> Iterator[tuple[TableCellKey, etree._Element]]:
    """Iterate over table cells, yielding the first paragraph in each cell.
    
    Args:
        table_element: A w:tbl element
        table_idx: The 0-based table index in the document
        
    Yields:
        Tuples of (TableCellKey, first_paragraph_element) for each cell
    """
    rows = table_element.findall(qn("w:tr"))
    for row_idx, row in enumerate(rows):
        cells = row.findall(qn("w:tc"))
        for col_idx, cell in enumerate(cells):
            # Find first paragraph in cell
            first_para = cell.find(qn("w:p"))
            if first_para is not None:
                yield TableCellKey(table_idx, row_idx, col_idx), first_para
            else:
                # Check for nested SDT containing paragraph
                for sdt in cell.findall(qn("w:sdt")):
                    sdt_content = sdt.find(qn("w:sdtContent"))
                    if sdt_content is not None:
                        first_para = sdt_content.find(qn("w:p"))
                        if first_para is not None:
                            yield TableCellKey(table_idx, row_idx, col_idx), first_para
                            break


def _block_to_key(block: dict) -> BlockKey | None:
    """Convert a block dict to its corresponding BlockKey.
    
    Args:
        block: A block dict from blocks.jsonl
        
    Returns:
        ParaKey for paragraphs, TableCellKey for table cells, None if invalid
    """
    # Check for table cell block
    table_info = block.get("table")
    if table_info is not None:
        # Table cell block: has table.table_id, table.row, table.col
        table_id = table_info.get("table_id", "")
        # Extract table index from table_id (e.g., "tbl_0" -> 0)
        if table_id.startswith("tbl_"):
            try:
                table_idx = int(table_id[4:])
            except ValueError:
                return None
        else:
            return None
        
        row = table_info.get("row")
        col = table_info.get("col")
        if row is not None and col is not None:
            return TableCellKey(table_idx, row, col)
        return None
    
    # Check for paragraph block
    para_idx = block.get("para_idx")
    if para_idx is not None:
        return ParaKey(para_idx)
    
    return None


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
    paragraphs by their location:
    - Top-level paragraphs: matched by "para_idx" field
    - Table cells: matched by "table" field (table_id, row, col)

    Args:
        doc_or_path: Document object or path to .docx file
        blocks: List of block dicts with "id" and either "para_idx" or "table" fields
        overwrite: If True, overwrite existing UUIDs; if False, skip already-wrapped paragraphs

    Returns:
        Mapping of block_id to location string for successfully embedded blocks
        (location is "para_N" for paragraphs or "tbl_T_r_R_c_C" for table cells)
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
        save_path = Path(doc_or_path)
    else:
        document = doc_or_path
        save_path = None

    # Build index of BlockKey -> paragraph element
    key_to_element: dict[BlockKey, etree._Element] = {}
    for key, elem in _iter_all_blocks(document):
        key_to_element[key] = elem

    embedded: dict[str, str] = {}

    for block in blocks:
        block_id = block.get("id")
        if block_id is None:
            continue

        # Convert block to key
        block_key = _block_to_key(block)
        if block_key is None:
            continue

        para_elem = key_to_element.get(block_key)
        if para_elem is None:
            continue

        # Check if already has UUID
        existing = get_paragraph_uuid(para_elem)
        if existing is not None and not overwrite:
            embedded[block_id] = _key_to_location_string(block_key)
            continue

        # Embed UUID
        if set_paragraph_uuid(document, para_elem, block_id):
            embedded[block_id] = _key_to_location_string(block_key)

    # Save if we loaded from path
    if save_path is not None:
        document.save(str(save_path))

    return embedded


def _key_to_location_string(key: BlockKey) -> str:
    """Convert a BlockKey to a human-readable location string."""
    if isinstance(key, ParaKey):
        return f"para_{key.para_idx}"
    elif isinstance(key, TableCellKey):
        return f"tbl_{key.table_idx}_r_{key.row}_c_{key.col}"
    return "unknown"


def extract_block_uuids(doc_or_path: Document | str | "Path") -> dict[str, BlockKey]:
    """Extract UUID → BlockKey mapping from embedded content controls.

    Args:
        doc_or_path: Document object or path to .docx file

    Returns:
        Mapping of UUID string to BlockKey (ParaKey or TableCellKey)
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
    else:
        document = doc_or_path

    uuid_to_key: dict[str, BlockKey] = {}

    for key, para_elem in _iter_all_blocks(document):
        uuid_val = get_paragraph_uuid(para_elem)
        if uuid_val is not None:
            uuid_to_key[uuid_val] = key

    return uuid_to_key


def extract_block_uuids_legacy(doc_or_path: Document | str | "Path") -> dict[str, int]:
    """Extract UUID → paragraph index mapping from embedded content controls.
    
    Legacy function for backward compatibility. Only returns top-level paragraphs.
    For full support including table cells, use extract_block_uuids().

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
