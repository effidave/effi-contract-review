from __future__ import annotations

from pathlib import Path
import zipfile

from lxml import etree


def parse_docx_parts(docx_path: Path):
    """Extract the WordprocessingML XML parts that drive numbering analysis."""
    if not docx_path.exists():
        raise FileNotFoundError(f"{docx_path} does not exist")

    with zipfile.ZipFile(docx_path, "r") as archive:

        def _load(part: str):
            try:
                with archive.open(part) as stream:
                    return etree.parse(stream)
            except KeyError as exc:
                raise FileNotFoundError(f"{part} missing in {docx_path}") from exc

        return (
            _load("word/document.xml"),
            _load("word/numbering.xml"),
            _load("word/styles.xml"),
        )
