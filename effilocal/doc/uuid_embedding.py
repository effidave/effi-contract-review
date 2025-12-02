"""Paragraph identification via native Word w14:paraId.

This module provides functions to work with Word's native paragraph IDs
(w14:paraId) for block tracking and matching. These are 8-character hex 
values that Word assigns to every paragraph and preserves across edits.

Key advantages of w14:paraId over custom embedding:
- Already present on all paragraphs - no embedding needed
- 100% schema-compliant - no corruption risk
- Preserved by Word across save/close/reopen cycles
- Works with python-docx without modification

The block "id" field in blocks.jsonl stores the w14:paraId directly.
When matching blocks between analysis runs, we use:
1. w14:paraId match (primary - most reliable)
2. Content hash match (fallback for modified content)
3. Position match (last resort for heavily modified documents)
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
    "extract_block_para_ids",
    "extract_block_uuids",  # Backward compatibility alias
    "extract_block_uuids_legacy",
    "get_paragraph_para_id",
    "get_paragraph_uuid",  # Backward compatibility alias
    "find_paragraph_by_para_id",
    "assign_block_ids",
    "BlockKey",
    "ParaKey",
    "TableCellKey",
    # Deprecated functions (no-ops, kept for backward compatibility)
    "embed_block_uuids",
    "remove_all_uuid_tags",
    "remove_all_uuid_controls",
    "set_paragraph_uuid",
    "EFFI_TAG_PREFIX",
]

# Legacy prefix kept for backward compatibility (no longer used)
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


def get_paragraph_para_id(paragraph_element: etree._Element) -> str | None:
    """Get the w14:paraId from a paragraph element.

    Args:
        paragraph_element: A w:p element

    Returns:
        The 8-character hex paraId if present, else None
    """
    return paragraph_element.get(qn("w14:paraId"))


# Backward compatibility alias
get_paragraph_uuid = get_paragraph_para_id


def find_paragraph_by_para_id(doc: Document, para_id: str):
    """Find a paragraph by its w14:paraId.
    
    Args:
        doc: Document object
        para_id: The 8-character hex paraId to find
        
    Returns:
        Paragraph object or None if not found
    """
    target_id = para_id.upper()
    
    # Search body paragraphs
    for para in doc.paragraphs:
        pid = para._element.get(qn("w14:paraId"))
        if pid and pid.upper() == target_id:
            return para
    
    # Search table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    pid = para._element.get(qn("w14:paraId"))
                    if pid and pid.upper() == target_id:
                        return para
    
    return None


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


def _iter_all_blocks(document: Document) -> Iterator[tuple[BlockKey, etree._Element]]:
    """Iterate over ALL paragraph elements in the document, including those in tables.
    
    Yields tuples of (BlockKey, paragraph_element) where BlockKey is either:
    - ParaKey(para_idx) for top-level body paragraphs
    - TableCellKey(table_idx, row, col) for paragraphs inside table cells
    
    This traverses:
    - Top-level body paragraphs
    - Tables → rows → cells → paragraphs
    
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


def _key_to_location_string(key: BlockKey) -> str:
    """Convert a BlockKey to a human-readable location string."""
    if isinstance(key, ParaKey):
        return f"para_{key.para_idx}"
    elif isinstance(key, TableCellKey):
        return f"tbl_{key.table_idx}_r_{key.row}_c_{key.col}"
    return "unknown"


def extract_block_para_ids(doc_or_path: Document | str | "Path") -> dict[str, BlockKey]:
    """Extract para_id → BlockKey mapping from document.

    This reads the native w14:paraId from each paragraph.

    Args:
        doc_or_path: Document object or path to .docx file

    Returns:
        Mapping of para_id string to BlockKey (ParaKey or TableCellKey)
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
    else:
        document = doc_or_path

    para_id_to_key: dict[str, BlockKey] = {}

    for key, para_elem in _iter_all_blocks(document):
        para_id = get_paragraph_para_id(para_elem)
        if para_id:
            para_id_to_key[para_id] = key

    return para_id_to_key


# Backward compatibility alias
extract_block_uuids = extract_block_para_ids


def extract_block_uuids_legacy(doc_or_path: Document | str | "Path") -> dict[str, int]:
    """Extract para_id → paragraph index mapping from document.
    
    Legacy function for backward compatibility. Only returns top-level paragraphs.
    For full support including table cells, use extract_block_para_ids().

    Args:
        doc_or_path: Document object or path to .docx file

    Returns:
        Mapping of para_id string to paragraph index (0-based)
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
    else:
        document = doc_or_path

    para_id_to_idx: dict[str, int] = {}

    for idx, para_elem in _iter_paragraphs_with_index(document):
        para_id = get_paragraph_para_id(para_elem)
        if para_id:
            para_id_to_idx[para_id] = idx

    return para_id_to_idx


# ============================================================================
# Deprecated functions - kept for backward compatibility (no-ops)
# ============================================================================

def embed_block_uuids(
    doc_or_path: Document | str | "Path",
    blocks: list[dict],
    *,
    overwrite: bool = False,
) -> dict[str, str]:
    """DEPRECATED: No longer needed - we use native w14:paraId instead.
    
    This function now just returns a mapping of block IDs to their para_ids,
    without modifying the document.
    """
    from pathlib import Path

    if isinstance(doc_or_path, (str, Path)):
        document = Document(str(doc_or_path))
    else:
        document = doc_or_path

    # Build index of BlockKey -> paragraph element
    key_to_element: dict[BlockKey, etree._Element] = {}
    for key, elem in _iter_all_blocks(document):
        key_to_element[key] = elem

    result: dict[str, str] = {}

    for block in blocks:
        block_id = block.get("id")
        para_id = block.get("para_id")
        if block_id and para_id:
            result[block_id] = para_id

    return result


def set_paragraph_uuid(
    document: Document,
    paragraph_element: etree._Element,
    uuid_value: str,
) -> bool:
    """DEPRECATED: No longer needed - we use native w14:paraId instead.
    
    This is a no-op kept for backward compatibility.
    """
    return True


def remove_all_uuid_tags(doc_or_path: Document | str | "Path") -> int:
    """DEPRECATED: No longer needed - we use native w14:paraId instead.
    
    This is a no-op kept for backward compatibility.
    Returns 0 (nothing removed).
    """
    return 0


# Backward compatibility alias
remove_all_uuid_controls = remove_all_uuid_tags


def assign_block_ids(
    blocks: list[dict],
    para_id_map: dict[str, BlockKey] | None = None,
    old_blocks: list[dict] | None = None,
    position_threshold: int = 5,
    # Deprecated parameter (backward compat)
    embedded_uuids: dict[str, BlockKey] | None = None,
) -> dict[str, str]:
    """Assign IDs to blocks that have id=None.
    
    Since we now use w14:paraId as the block ID, this function simply
    copies para_id to id for each block that doesn't have one.
    
    For matching between analysis runs:
    1. para_id match: If block has same para_id as old block, reuse old ID
    2. Content hash match: If block has same content_hash, reuse old ID
    3. Position match: Match nearby blocks with same type
    4. Generate new: Use para_id as the new ID (or generate UUID as fallback)
    
    Args:
        blocks: List of block dicts. Blocks with id=None will be assigned IDs.
        para_id_map: Optional para_id → BlockKey mapping (currently unused).
        old_blocks: Previous blocks.jsonl content for matching.
        position_threshold: Maximum distance for position matching.
        embedded_uuids: DEPRECATED - use para_id_map instead.
    
    Returns:
        Stats dict with counts: {"from_para_id": N, "from_hash": N, 
                                  "from_position": N, "generated": N}
    
    Mutates blocks in place to set the "id" field.
    """
    # Handle deprecated parameter
    effective_para_id_map = embedded_uuids if embedded_uuids is not None else para_id_map
    _ = effective_para_id_map  # Currently unused but kept for interface consistency
    
    stats = {"from_para_id": 0, "from_hash": 0, "from_position": 0, "generated": 0}
    
    # Build mappings from old blocks for matching
    old_para_id_to_block: dict[str, dict] = {}
    hash_to_old_id: dict[str, str] = {}
    old_blocks_by_position: dict[int, dict] = {}
    
    if old_blocks:
        for old_block in old_blocks:
            old_id = old_block.get("id")
            old_para_id = old_block.get("para_id")
            old_hash = old_block.get("content_hash")
            
            # Index by para_id for primary matching
            if old_para_id:
                old_para_id_to_block[old_para_id] = old_block
            
            # Index by hash for content matching
            if old_id and old_hash and old_hash not in hash_to_old_id:
                hash_to_old_id[old_hash] = old_id
            
            # Index by position for fallback matching
            para_idx = old_block.get("para_idx")
            if para_idx is not None and old_id:
                old_blocks_by_position[para_idx] = old_block
    
    # Track which old IDs have been used
    used_ids: set[str] = set()
    
    # First pass: para_id and hash matching
    unmatched_blocks: list[dict] = []
    for block in blocks:
        # Skip blocks that already have an ID
        if block.get("id") is not None:
            continue
        
        para_id = block.get("para_id")
        
        # Priority 1: Match by para_id
        if para_id and para_id in old_para_id_to_block:
            old_block = old_para_id_to_block[para_id]
            old_id = old_block.get("id")
            if old_id and old_id not in used_ids:
                block["id"] = old_id
                used_ids.add(old_id)
                stats["from_para_id"] += 1
                continue
        
        # Priority 2: Match by content hash
        content_hash = block.get("content_hash")
        if content_hash and content_hash in hash_to_old_id:
            old_id = hash_to_old_id[content_hash]
            if old_id not in used_ids:
                block["id"] = old_id
                used_ids.add(old_id)
                stats["from_hash"] += 1
                continue
        
        # Couldn't match yet
        unmatched_blocks.append(block)
    
    # Second pass: position-based matching
    for block in unmatched_blocks:
        if block.get("id") is not None:
            continue
        
        para_idx = block.get("para_idx")
        if para_idx is not None and old_blocks_by_position:
            # Look for nearby old blocks within threshold
            best_match = None
            best_distance = position_threshold + 1
            
            for offset in range(position_threshold + 1):
                for check_idx in [para_idx + offset, para_idx - offset]:
                    if check_idx in old_blocks_by_position:
                        old_block = old_blocks_by_position[check_idx]
                        old_id = old_block.get("id")
                        if (old_id and 
                            old_id not in used_ids and
                            old_block.get("type") == block.get("type")):
                            distance = abs(check_idx - para_idx)
                            if distance < best_distance:
                                best_match = old_block
                                best_distance = distance
            
            if best_match:
                block["id"] = best_match["id"]
                used_ids.add(block["id"])
                stats["from_position"] += 1
                continue
        
        # Priority 4: Use para_id as the ID, or generate new UUID
        para_id = block.get("para_id")
        if para_id and para_id not in used_ids:
            block["id"] = para_id
            used_ids.add(para_id)
            stats["generated"] += 1
        else:
            # Fallback: generate UUID
            new_id = str(uuid4())
            block["id"] = new_id
            used_ids.add(new_id)
            stats["generated"] += 1
    
    return stats
