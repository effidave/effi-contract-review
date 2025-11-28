from __future__ import annotations

from pathlib import Path
from typing import Iterable

from effilocal.doc.direct_docx import iter_paragraph_blocks


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / name


def _list_blocks(doc_path: Path) -> Iterable[dict]:
    return (block for block in iter_paragraph_blocks(doc_path) if block.get("list"))


def test_restart_groups_split_on_explicit_restart() -> None:
    blocks = list(_list_blocks(_fixture("numbering_restart.docx")))
    assert blocks, "Expected list blocks in numbering_restart.docx"

    seen_groups: list[str] = []
    current_group = None

    for block in blocks:
        list_payload = block["list"]
        group_id = block["restart_group_id"]

        assert group_id, "List block must carry a restart_group_id"

        if group_id != current_group:
            assert list_payload["restart_boundary"] is True
            assert list_payload["level"] == 0
            seen_groups.append(group_id)
            current_group = group_id
        else:
            assert list_payload["restart_boundary"] is False

    assert len(seen_groups) >= 2, "Expected multiple restart groups in fixture"
