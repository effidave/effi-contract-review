"""Test that interleaved lists increment ordinals sequentially in document order."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from effilocal.doc.direct_docx import iter_paragraph_blocks


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / name


def _list_blocks(doc_path: Path) -> Iterable[dict]:
    return (block for block in iter_paragraph_blocks(doc_path) if block.get("list"))


def test_interleaved_lists_increment_sequentially() -> None:
    """
    Test that numbering_restart.docx has sequentially increasing ordinals
    even when lists are interleaved at the same level.
    
    Word renders interleaved lists at level 0 with the same numId/abstractNumId
    as sequential: 1., 2., 3., 4., 5., 6., etc. in document order,
    regardless of which restart group they belong to.
    """
    blocks = list(_list_blocks(_fixture("numbering_restart.docx")))
    assert blocks, "Expected list blocks in numbering_restart.docx"

    # Collect all level-0 blocks in document order
    level_0_blocks = [b for b in blocks if b["list"]["level"] == 0]
    
    assert len(level_0_blocks) >= 2, "Expected at least 2 level-0 blocks"
    
    # Extract ordinals and parse the numeric part
    ordinals = []
    for block in level_0_blocks:
        ordinal = block["list"]["ordinal"]
        # Parse numeric value (e.g., "1.", "2.", "3.")
        if ordinal.endswith("."):
            try:
                num = int(ordinal[:-1])
                ordinals.append((num, ordinal, block["id"]))
            except ValueError:
                pass  # Skip non-numeric ordinals
    
    assert len(ordinals) >= 2, "Expected at least 2 numeric ordinals"
    
    # Verify ordinals increment sequentially: 1, 2, 3, 4, ...
    expected = 1
    for num, ordinal, block_id in ordinals:
        assert num == expected, (
            f"Block {block_id} has ordinal '{ordinal}' (value {num}) "
            f"but expected '{expected}.' in document order"
        )
        expected += 1
    
    print(f"\n[OK] All {len(ordinals)} level-0 blocks have sequential ordinals: "
          f"{', '.join(ord for _, ord, _ in ordinals)}")
