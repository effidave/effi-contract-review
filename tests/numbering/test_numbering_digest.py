from __future__ import annotations

from pathlib import Path

from effilocal.doc.direct_docx import iter_paragraph_blocks


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / name


def _list_items(doc_path: Path) -> list[dict]:
    return [block for block in iter_paragraph_blocks(doc_path) if block.get("list")]


def test_digest_differs_for_different_numbering_schema() -> None:
    decimal = _list_items(_fixture("numbering_decimal.docx"))
    roman = _list_items(_fixture("numbering_roman.docx"))

    assert decimal and roman

    decimal_digest = decimal[0]["list"]["numbering_digest"]
    roman_digest = roman[0]["list"]["numbering_digest"]

    assert decimal_digest != roman_digest


def test_digest_stable_with_cosmetic_text_change(tmp_path: Path) -> None:
    fixture = _fixture("numbering_decimal.docx")
    original = _list_items(fixture)
    assert original
    original_digest = original[0]["list"]["numbering_digest"]

    modified = tmp_path / "modified.docx"
    modified.write_bytes(fixture.read_bytes().replace(b"Item", b"Clause"))

    updated = _list_items(modified)
    assert updated

    assert updated[0]["list"]["numbering_digest"] == original_digest
