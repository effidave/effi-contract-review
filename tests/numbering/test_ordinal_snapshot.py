from __future__ import annotations

from pathlib import Path

from effilocal.doc.direct_docx import iter_paragraph_blocks


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / name


def test_ordinal_snapshot_stable_across_rerun(tmp_path: Path) -> None:
    fixture = _fixture("numbering_decimal.docx")
    first = [block for block in iter_paragraph_blocks(fixture) if block.get("list")]
    assert first

    original_snapshot = first[0]["list"]["ordinal_at_parse"]

    modified = tmp_path / "modified.docx"
    modified.write_bytes(fixture.read_bytes().replace(b"Item", b"New Item"))

    second = [block for block in iter_paragraph_blocks(modified) if block.get("list")]
    assert second

    assert second[0]["list"]["ordinal_at_parse"] == original_snapshot
