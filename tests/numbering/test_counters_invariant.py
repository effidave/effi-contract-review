from __future__ import annotations

from pathlib import Path

from effilocal.doc.direct_docx import iter_paragraph_blocks


FIXTURES = [
    "simple.docx",
    "numbering_decimal.docx",
    "numbering_restart.docx",
    "numbering_roman.docx",
    "lists.docx",
    "mixed.docx",
    "real_world/messy_contract.docx",
]


def _fixture_path(name: str) -> Path:
    base = Path(__file__).resolve().parent.parent / "fixtures"
    return base / name


def test_counters_length_matches_level() -> None:
    for name in FIXTURES:
        path = _fixture_path(name)
        assert path.exists(), f"Fixture missing: {name}"
        for block in iter_paragraph_blocks(path):
            list_payload = block.get("list")
            if not list_payload:
                continue
            level = int(list_payload["level"])
            counters = list_payload["counters"]
            assert len(counters) == level + 1, (
                f"Fixture {name}: block {block['id']} has counters {counters} at level {level}"
            )
