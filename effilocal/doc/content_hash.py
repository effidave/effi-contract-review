"""Content hash utilities for block matching fallback.

When UUIDs are lost (e.g., content controls stripped by Word operations),
content hashes provide a fallback mechanism to match blocks between the
old analysis and a re-analyzed document.

This module extends effilocal.util.hash with block-level matching logic.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Union

from effilocal.doc.uuid_embedding import BlockKey, ParaKey, TableCellKey
from effilocal.util.hash import norm_text_hash

__all__ = [
    "compute_block_hash",
    "match_blocks_by_hash",
    "BlockMatch",
    "MatchResult",
]


def compute_block_hash(text: str) -> str:
    """Compute SHA-256 of normalized text for block matching.

    This is a thin wrapper around norm_text_hash for clarity.

    Args:
        text: The raw text content of a block

    Returns:
        Hash in format "sha256:<hex>"
    """
    return norm_text_hash(text)


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
        table_id = table_info.get("table_id", "")
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


@dataclass(frozen=True, slots=True)
class BlockMatch:
    """Represents a matched pair of blocks."""

    old_id: str
    new_id: str
    method: str  # "para_id", "hash", "position"
    confidence: float  # 0.0-1.0


@dataclass(slots=True)
class MatchResult:
    """Result of block matching operation."""

    matches: list[BlockMatch]
    unmatched_old: list[str]  # IDs of old blocks that couldn't be matched
    unmatched_new: list[str]  # IDs of new blocks that couldn't be matched

    @property
    def matched_by_para_id(self) -> int:
        """Count of blocks matched by para_id."""
        return sum(1 for m in self.matches if m.method == "para_id")

    @property
    def matched_by_uuid(self) -> int:
        """Count of blocks matched by para_id (deprecated alias)."""
        return self.matched_by_para_id

    @property
    def matched_by_hash(self) -> int:
        """Count of blocks matched by hash."""
        return sum(1 for m in self.matches if m.method == "hash")

    @property
    def matched_by_position(self) -> int:
        """Count of blocks matched by position heuristics."""
        return sum(1 for m in self.matches if m.method == "position")

    def to_delta_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for analysis_delta.json."""
        return {
            "matched_by_para_id": self.matched_by_para_id,
            "matched_by_hash": self.matched_by_hash,
            "matched_by_position": self.matched_by_position,
            "new_blocks": self.unmatched_new,
            "deleted_blocks": self.unmatched_old,
        }


def match_blocks_by_hash(
    old_blocks: list[dict],
    new_blocks: list[dict],
    *,
    id_field: str = "id",
    hash_field: str = "content_hash",
    text_field: str = "text",
    para_id_map: dict[str, BlockKey] | None = None,
    # Deprecated parameter names (backward compat)
    uuid_field: str | None = None,
    embedded_uuids: dict[str, BlockKey] | None = None,
) -> MatchResult:
    """Match blocks using para_id, hash, and position heuristics.

    Matching priority:
    1. Para_id match: If new block's position matches a para_id's BlockKey
    2. Hash match: If content hashes match (unique match preferred)
    3. Position match: For remaining unmatched, use position proximity

    Args:
        old_blocks: Blocks from previous analysis
        new_blocks: Blocks from current analysis
        id_field: Field name for block ID
        hash_field: Field name for content hash
        text_field: Field name for text content
        para_id_map: Optional mapping of para_id → BlockKey from document
        uuid_field: Deprecated, use id_field
        embedded_uuids: Deprecated, use para_id_map

    Returns:
        MatchResult with matched pairs and unmatched blocks
    """
    # Handle deprecated parameter names
    effective_id_field = uuid_field if uuid_field is not None else id_field
    effective_para_id_map = embedded_uuids if embedded_uuids is not None else para_id_map
    
    matches: list[BlockMatch] = []
    matched_old: set[str] = set()
    matched_new: set[str] = set()

    # Build lookup structures
    old_by_id: dict[str, dict] = {b[effective_id_field]: b for b in old_blocks if effective_id_field in b}
    old_by_hash: dict[str, list[dict]] = defaultdict(list)
    for block in old_blocks:
        h = block.get(hash_field) or (compute_block_hash(block.get(text_field, "")) if text_field in block else None)
        if h:
            old_by_hash[h].append(block)

    # Phase 1: Para_id matching (if para_id map provided)
    if effective_para_id_map:
        # Build reverse lookup: BlockKey → para_id
        key_to_para_id: dict[BlockKey, str] = {v: k for k, v in effective_para_id_map.items()}
        
        for new_block in new_blocks:
            new_id = new_block.get(effective_id_field)
            if new_id is None or new_id in matched_new:
                continue

            # Convert new block to its key
            new_key = _block_to_key(new_block)
            if new_key is None:
                continue

            # Check if this position has a para_id
            para_id = key_to_para_id.get(new_key)
            if para_id and para_id in old_by_id:
                matches.append(
                    BlockMatch(
                        old_id=para_id,
                        new_id=new_id,
                        method="para_id",
                        confidence=1.0,
                    )
                )
                matched_old.add(para_id)
                matched_new.add(new_id)

    # Phase 2: Hash matching
    for new_block in new_blocks:
        new_id = new_block.get(effective_id_field)
        if new_id is None or new_id in matched_new:
            continue

        new_hash = new_block.get(hash_field) or (
            compute_block_hash(new_block.get(text_field, "")) if text_field in new_block else None
        )
        if not new_hash:
            continue

        candidates = old_by_hash.get(new_hash, [])
        unmatched_candidates = [c for c in candidates if c[effective_id_field] not in matched_old]

        if len(unmatched_candidates) == 1:
            # Unique hash match - high confidence
            old_id = unmatched_candidates[0][effective_id_field]
            matches.append(
                BlockMatch(
                    old_id=old_id,
                    new_id=new_id,
                    method="hash",
                    confidence=0.95,
                )
            )
            matched_old.add(old_id)
            matched_new.add(new_id)
        elif len(unmatched_candidates) > 1:
            # Multiple candidates - use position to disambiguate
            new_key = _block_to_key(new_block)
            new_idx = _get_position_index(new_key)
            best_candidate = None
            best_distance = float("inf")

            for candidate in unmatched_candidates:
                old_key = _block_to_key(candidate)
                old_idx = _get_position_index(old_key)
                distance = abs(old_idx - new_idx)
                if distance < best_distance:
                    best_distance = distance
                    best_candidate = candidate

            if best_candidate is not None:
                old_id = best_candidate[effective_id_field]
                # Lower confidence due to ambiguity
                confidence = max(0.7, 0.95 - (best_distance * 0.05))
                matches.append(
                    BlockMatch(
                        old_id=old_id,
                        new_id=new_id,
                        method="hash",
                        confidence=confidence,
                    )
                )
                matched_old.add(old_id)
                matched_new.add(new_id)

    # Phase 3: Position-based matching for remaining blocks
    remaining_old = [b for b in old_blocks if b.get(effective_id_field) not in matched_old]
    remaining_new = [b for b in new_blocks if b.get(effective_id_field) not in matched_new]

    # Sort by position index
    remaining_old_sorted = sorted(remaining_old, key=lambda b: _get_position_index(_block_to_key(b)))
    remaining_new_sorted = sorted(remaining_new, key=lambda b: _get_position_index(_block_to_key(b)))

    # Simple positional alignment for remaining blocks
    # Only match if positions are close and text is similar
    for old_block in remaining_old_sorted:
        old_id = old_block.get(effective_id_field)
        if old_id is None or old_id in matched_old:
            continue

        old_key = _block_to_key(old_block)
        old_idx = _get_position_index(old_key)
        old_text = old_block.get(text_field, "")

        best_match = None
        best_score = 0.0

        for new_block in remaining_new_sorted:
            new_id = new_block.get(effective_id_field)
            if new_id is None or new_id in matched_new:
                continue

            new_key = _block_to_key(new_block)
            new_idx = _get_position_index(new_key)
            new_text = new_block.get(text_field, "")

            # Calculate position proximity score
            position_distance = abs(old_idx - new_idx)
            if position_distance > 5:  # Don't match if too far apart
                continue

            position_score = max(0, 1.0 - (position_distance * 0.15))

            # Calculate text similarity (simple approach)
            text_score = _text_similarity(old_text, new_text)

            # Combined score
            combined_score = (position_score * 0.4) + (text_score * 0.6)

            if combined_score > best_score and combined_score > 0.5:
                best_score = combined_score
                best_match = new_block

        if best_match is not None:
            new_id = best_match.get(effective_id_field)
            matches.append(
                BlockMatch(
                    old_id=old_id,
                    new_id=new_id,
                    method="position",
                    confidence=best_score * 0.8,  # Cap at 0.8 for position matches
                )
            )
            matched_old.add(old_id)
            matched_new.add(new_id)

    # Collect unmatched blocks
    unmatched_old = [b[effective_id_field] for b in old_blocks if b.get(effective_id_field) not in matched_old]
    unmatched_new = [b[effective_id_field] for b in new_blocks if b.get(effective_id_field) not in matched_new]

    return MatchResult(
        matches=matches,
        unmatched_old=unmatched_old,
        unmatched_new=unmatched_new,
    )


def _get_position_index(key: BlockKey | None) -> int:
    """Get a numeric position index from a BlockKey for sorting/comparison.
    
    For paragraphs, returns the para_idx.
    For table cells, returns a composite index that accounts for table, row, col.
    """
    if key is None:
        return 0
    if isinstance(key, ParaKey):
        return key.para_idx
    if isinstance(key, TableCellKey):
        # Composite index: table_idx * 10000 + row * 100 + col
        # This keeps table cells grouped and ordered
        return key.table_idx * 10000 + key.row * 100 + key.col
    return 0


def _text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score.

    Uses word overlap as a simple similarity metric.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    # Normalize and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0
