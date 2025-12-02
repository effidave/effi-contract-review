"""Content hash utilities for block matching fallback.

When UUIDs are lost (e.g., content controls stripped by Word operations),
content hashes provide a fallback mechanism to match blocks between the
old analysis and a re-analyzed document.

This module extends effilocal.util.hash with block-level matching logic.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

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


@dataclass(frozen=True, slots=True)
class BlockMatch:
    """Represents a matched pair of blocks."""

    old_id: str
    new_id: str
    method: str  # "uuid", "hash", "position"
    confidence: float  # 0.0-1.0


@dataclass(slots=True)
class MatchResult:
    """Result of block matching operation."""

    matches: list[BlockMatch]
    unmatched_old: list[str]  # IDs of old blocks that couldn't be matched
    unmatched_new: list[str]  # IDs of new blocks that couldn't be matched

    @property
    def matched_by_uuid(self) -> int:
        """Count of blocks matched by UUID."""
        return sum(1 for m in self.matches if m.method == "uuid")

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
            "matched_by_uuid": self.matched_by_uuid,
            "matched_by_hash": self.matched_by_hash,
            "matched_by_position": self.matched_by_position,
            "new_blocks": self.unmatched_new,
            "deleted_blocks": self.unmatched_old,
        }


def match_blocks_by_hash(
    old_blocks: list[dict],
    new_blocks: list[dict],
    *,
    uuid_field: str = "id",
    hash_field: str = "content_hash",
    text_field: str = "text",
    embedded_uuids: dict[str, int] | None = None,
) -> MatchResult:
    """Match blocks using UUID, hash, and position heuristics.

    Matching priority:
    1. UUID match: If new block's embedded UUID matches an old block's ID
    2. Hash match: If content hashes match (unique match preferred)
    3. Position match: For remaining unmatched, use position proximity

    Args:
        old_blocks: Blocks from previous analysis
        new_blocks: Blocks from current analysis
        uuid_field: Field name for block ID
        hash_field: Field name for content hash
        text_field: Field name for text content
        embedded_uuids: Optional mapping of UUID → paragraph index from document

    Returns:
        MatchResult with matched pairs and unmatched blocks
    """
    matches: list[BlockMatch] = []
    matched_old: set[str] = set()
    matched_new: set[str] = set()

    # Build lookup structures
    old_by_id: dict[str, dict] = {b[uuid_field]: b for b in old_blocks if uuid_field in b}
    old_by_hash: dict[str, list[dict]] = defaultdict(list)
    for block in old_blocks:
        h = block.get(hash_field) or (compute_block_hash(block.get(text_field, "")) if text_field in block else None)
        if h:
            old_by_hash[h].append(block)

    # Phase 1: UUID matching (if embedded UUIDs provided)
    if embedded_uuids:
        for new_block in new_blocks:
            new_id = new_block.get(uuid_field)
            para_idx = new_block.get("para_idx")

            if new_id is None or para_idx is None:
                continue

            # Check if this paragraph position has an embedded UUID
            for embedded_uuid, emb_idx in embedded_uuids.items():
                if emb_idx == para_idx and embedded_uuid in old_by_id:
                    matches.append(
                        BlockMatch(
                            old_id=embedded_uuid,
                            new_id=new_id,
                            method="uuid",
                            confidence=1.0,
                        )
                    )
                    matched_old.add(embedded_uuid)
                    matched_new.add(new_id)
                    break

    # Phase 2: Hash matching
    for new_block in new_blocks:
        new_id = new_block.get(uuid_field)
        if new_id is None or new_id in matched_new:
            continue

        new_hash = new_block.get(hash_field) or (
            compute_block_hash(new_block.get(text_field, "")) if text_field in new_block else None
        )
        if not new_hash:
            continue

        candidates = old_by_hash.get(new_hash, [])
        unmatched_candidates = [c for c in candidates if c[uuid_field] not in matched_old]

        if len(unmatched_candidates) == 1:
            # Unique hash match - high confidence
            old_id = unmatched_candidates[0][uuid_field]
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
            new_idx = new_block.get("para_idx", 0)
            best_candidate = None
            best_distance = float("inf")

            for candidate in unmatched_candidates:
                # Try to find position from old analysis
                old_idx = candidate.get("para_idx", 0)
                distance = abs(old_idx - new_idx)
                if distance < best_distance:
                    best_distance = distance
                    best_candidate = candidate

            if best_candidate is not None:
                old_id = best_candidate[uuid_field]
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
    remaining_old = [b for b in old_blocks if b.get(uuid_field) not in matched_old]
    remaining_new = [b for b in new_blocks if b.get(uuid_field) not in matched_new]

    # Sort by position
    remaining_old_sorted = sorted(remaining_old, key=lambda b: b.get("para_idx", 0))
    remaining_new_sorted = sorted(remaining_new, key=lambda b: b.get("para_idx", 0))

    # Simple positional alignment for remaining blocks
    # Only match if positions are close and text is similar
    for old_block in remaining_old_sorted:
        old_id = old_block.get(uuid_field)
        if old_id is None or old_id in matched_old:
            continue

        old_idx = old_block.get("para_idx", 0)
        old_text = old_block.get(text_field, "")

        best_match = None
        best_score = 0.0

        for new_block in remaining_new_sorted:
            new_id = new_block.get(uuid_field)
            if new_id is None or new_id in matched_new:
                continue

            new_idx = new_block.get("para_idx", 0)
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
            new_id = best_match.get(uuid_field)
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
    unmatched_old = [b[uuid_field] for b in old_blocks if b.get(uuid_field) not in matched_old]
    unmatched_new = [b[uuid_field] for b in new_blocks if b.get(uuid_field) not in matched_new]

    return MatchResult(
        matches=matches,
        unmatched_old=unmatched_old,
        unmatched_new=unmatched_new,
    )


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
