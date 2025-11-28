from __future__ import annotations

from pathlib import Path

from effilocal.doc.direct_docx import iter_paragraph_blocks


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / name


def _list_items(doc_path: Path) -> list[dict]:
    return [block for block in iter_paragraph_blocks(doc_path) if block.get("list")]


def test_instance_id_stable_across_reparse() -> None:
    first_pass = _list_items(_fixture("numbering_decimal.docx"))
    second_pass = _list_items(_fixture("numbering_decimal.docx"))

    assert first_pass and second_pass
    ids_first = [block["list"]["list_instance_id"] for block in first_pass]
    ids_second = [block["list"]["list_instance_id"] for block in second_pass]

    assert ids_first == ids_second


def test_restart_changes_instance_id() -> None:
    blocks = _list_items(_fixture("numbering_restart.docx"))
    assert blocks

    instance_ids = []
    current = None
    for block in blocks:
        list_payload = block["list"]
        group = block["restart_group_id"]
        instance = list_payload["list_instance_id"]
        if group != current:
            instance_ids.append(instance)
            current = group

    assert len(set(instance_ids)) == len(instance_ids) >= 2
